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
> are partially delivered — see the Status column and per-story markers below. **EP38 onwards** is
> product-roadmap work, promoted into this backlog from
> [`../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md)
> as each epic is scheduled. EP35–EP37 and EP39–EP41 are still **proposals in the roadmap** and are
> deliberately **not** here yet.
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
| EP28 | Security Hardening (Architecture Review) | KAN-148 · KAN-149 · KAN-150 · KAN-151 · KAN-152 · KAN-153 | 🟡 In progress · ⏸ **deferred to final stage S5** (D-004; KAN-153 excepted) |
| EP29 | Data Layer & Query Performance | KAN-154 · KAN-155 · KAN-156 · KAN-157 · KAN-158 | 🟡 In progress |
| EP30 | Scalability & Runtime | KAN-159 · KAN-160 · KAN-161 · KAN-162 · KAN-163 · KAN-164 | ⬜ Planned |
| EP31 | Schema Source of Truth & Migrations | KAN-165 · KAN-166 · KAN-167 | 🟡 In progress |
| EP32 | Testing & CI Hardening | KAN-168 · KAN-169 · KAN-170 · KAN-171 | 🟡 In progress |
| EP33 | Frontend Modernization | KAN-172 · KAN-173 · KAN-174 · KAN-175 · KAN-176 · KAN-177 | ⬜ Planned · ⏸ **S5** (shares code with the escaping sweep; a11y applied as a design standard meanwhile — pending Q5) |
| EP34 | Architecture & Structure | KAN-178 · KAN-179 · KAN-180 · KAN-181 · KAN-182 | ⬜ Planned |
| EP38 | Employee Lifecycle Workflows | KAN-187 · KAN-183 · KAN-184 · KAN-185 · KAN-186 | 🟡 In progress · **first roadmap growth epic in the backlog** (BG4) — build stage **S3** (D-004); ✅ KAN-187 (audit), 🟡 KAN-185 (transfer); KAN-186 is **Later** |
| EP42 | Compensation, Job Architecture & Pay Equity | **W0** KAN-203 · KAN-204 · KAN-188 · KAN-189 · **W1** KAN-190 · KAN-191 · KAN-207 · **W2** KAN-199 · KAN-206 · KAN-210 · KAN-193 · KAN-194 · KAN-218 · KAN-195 · KAN-209 · **W3** KAN-196 · KAN-197 · KAN-198 · KAN-192 · **W4** KAN-200 · KAN-201 · KAN-202 · *(conditional)* KAN-208 | ⬜ Planned · **BG7** — W0 builds in **S2**, W1–W4 in **S3** (D-004). **23 stories in 5 waves** (A1 · Wave-5 · A2 · A3 · **A4–A6**). **⚠ A6 overturned the pay/step model**: the job decides the step, the step decides base pay, **pay never decides the step**. KAN-218 (additional pay) is new, KAN-209 is repurposed as the pay reconciliation, KAN-205 moved to Later, KAN-208 is conditional. Carries **KAN-203, a P0 Critical pre-existing defect fix** — **✅ landed 10 Aug 2026, DEF-42-4 + DEF-42-5 closed** — and **unblocks KAN-185** |
| EP44 | Performance Management | **P0** KAN-219 · KAN-220 · **P1** KAN-221 · KAN-222 · KAN-223 · **P2** KAN-224 · KAN-225 · KAN-226 · KAN-227 · KAN-228 · **P3** KAN-229 · KAN-230 · KAN-231 · KAN-232 · **P4** KAN-233 · KAN-234 · KAN-235 · KAN-236 · KAN-237 · **P5** KAN-238 · KAN-239 · KAN-240 | ⬜ Planned · **BG7** · **entered by A4/A5** — the owner chose full performance management over the 2-story input, **accepting the delay in his own words** (Decision D-006). **22 stories**, stage **S3**, **sequenced after EP42 and before EP43**. Outline depth — entering **S1**, not build. Carries the **EU AI Act / GDPR Art. 22 gate as stories (KAN-232, KAN-240), not notes**, and works-council inspectability (KAN-238) |
| EP43 | Annual Compensation Review Cycle | KAN-216 · KAN-211 · KAN-213 · KAN-214 · KAN-215 | ⬜ Planned · **BG7** · new in A2, **reduced by A6 from 7 stories to 5**. KAN-212 withdrawn (merged into KAN-216 and EP42's rate schedule); KAN-217 withdrawn (superseded by EP44). A6 collapsed the per-employee hike percentage, so this is now a **round-management** epic, not a differentiation one. **Sequenced last**, stage **S3**. **The natural descope if S3 runs long** |

> **EP28–EP34** are sourced from the architecture review in [`docs/ARCHITECTURE_REVIEW.md`](../ARCHITECTURE_REVIEW.md)
> (finding IDs `Fn` are referenced per story). Unlike EP1–EP27, these are **partially delivered**: ✅ KAN-152 · KAN-154 · KAN-157 · KAN-165 · KAN-169 done, 🟡 KAN-150 partial; the rest are ⬜ planned.
>
> **EP38** is the first **product-roadmap growth epic** promoted into this backlog — business goal **BG4,
> "Complete the people-ops lifecycle."** It is *not* architecture-review work and carries no `Fn` finding; its
> source is the roadmap's BG4 section. **The numbering is non-contiguous on purpose:** EP35–EP37 and EP39–EP41
> keep their roadmap numbers and stay proposals until they are scheduled, so the backlog no longer ends at EP34
> and will not renumber when they arrive.
>
> **BG7 is a three-epic programme and it runs in this order — `EP42 → EP44 → EP43`.** 23 + 22 + 5 = **50
> stories, ~8–9 months.** EP42 holds the pay record, the job ladder and the fairness check; **EP44 builds the
> review that produces the judgement** (the owner chose full performance management over a 2-story input and
> accepted the delay in his own words — Decision **D-006**); EP43 wraps the annual round. The ordering is his
> instruction — *"implement this first if required if this the blocker"* — applied to the hike cycle, not to
> the compensation record: **nothing in EP42 needs a performance rating.** **EP43 is the designated descope if
> S3 runs long**, and nothing is blocked while EP44 runs because EP42's KAN-210 lets a company move the whole
> ladder — which, under amendment A6, **is** the act of granting an across-the-board rise.
>
> **⚠ Story numbering after A4–A6:** KAN-218 is EP42's additional-pay story; **KAN-219 … KAN-240 are EP44**;
> KAN-205, KAN-212 and KAN-217 are withdrawn and recorded rather than reused. **The next free ID is KAN-241.**

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
> **⚠️ SEQUENCING CHANGED — SPM Decision D-004 (2026-08-09).** The **security & login** work is re-sequenced
> to the **final stage (S5)**, after all requirements are finalised and implemented. Severities below are
> unchanged — *order of execution* is what moved. Full reasoning + the trigger clause that reverses this:
> [`../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md)
> (amendment + §E) and `SPM_KICKOFF.md` §9 D-004.
>
> | Do **now** (S2 — enablers) | Do **last** (S5 — security & hardening sweep) |
> |---|---|
> | KAN-153 · KAN-155 · KAN-156 · KAN-158 · KAN-166 · KAN-167 · KAN-168 · KAN-170 · KAN-171 · KAN-178 | KAN-148 (as SSO) · KAN-149 · KAN-150→173 · KAN-151 · KAN-172 · KAN-174 · KAN-175 |
>
> **Standing rule while deferred:** new DOM code uses the existing global `escH()` helper, and the escaping
> already landed under KAN-150 is not to be reverted. The Production-Ready gate remains **NO-GO** throughout.
>
> **Delivered so far** (branch `chore/arch-review-and-hardening`, PR #2): **KAN-152** secure runtime
> defaults · **KAN-154 / KAN-157** missing indexes (migration 07) · **KAN-150** output escaping (4 of the
> highest-traffic screens; remainder → KAN-173) · **KAN-165** authoritative `schema.sql` baseline ·
> **KAN-169** GitHub Actions CI. Status shown in the Priority column below (✅ Done · 🟡 Partial).

## EP28 — Security Hardening  —  🟡 In progress · ⏸ **deferred to final stage S5 (D-004)**
**ID:** KAN-148 · **Label:** `security` `hardening` `pre-prod` `stage-S5`
**Description:** Close the authentication, CSRF, and output-escaping gaps and harden session, config, and
upload handling before the portal is exposed beyond local/demo use. Sourced from review findings F1–F5, F31.

> **⏸ Scheduling (SPM D-004, 2026-08-09):** KAN-148/149/150→173/151 are **not to be started now** — they run as
> one sweep in **S5**, after the functional backlog is complete and feature-frozen, because they are
> cross-cutting (~44 endpoints, every DOM builder) and every remaining epic adds to those same surfaces.
> **KAN-153 is the exception and stays in the current stage** (single-file config change, no feature coupling).
> **KAN-148 is to be delivered as SSO/OIDC** (roadmap EP40-S1), not throwaway password auth.
> **Escalation:** if the app becomes externally reachable (T1), gets real employee PII (T2), is demoed to a
> customer/prospect on real data (T3), or gets an account for anyone outside the build team (T4), these revert
> to **live P0** immediately.

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
| ✅ KAN-155 | As the **system**, I want composite writes to be atomic so a mid-loop failure cannot leave partial data. (F8) | A `transaction()` context manager (single commit/rollback) is added and used by vacation-type create/edit and org-change apply; per-row-loop commits removed; failure rolls back the whole unit; read paths no longer sit idle-in-transaction. | ✅ Done (ADR-006 — `app/db.py` `transaction()`; connections now `autocommit=True` so reads never sit idle-in-transaction and `execute()` no longer commits inside a block; wrapped: vacation-type create/edit, org-change `save_workflow` / `create_request` / `apply_change` / every `decide()` outcome incl. the final apply + close-out (TD-7). Evidence: pytest 4,524 pass · browser 77/77 · vacation 39/39 · `tests/test_transactions.py` (12, incl. a real-Postgres rollback tier). **Not** in scope, reported on: employee registration, role reassignment, company create, CSV import) |
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

---

# Product Roadmap Backlog (EP38+)

> Growth epics promoted from the SPM roadmap
> [`../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md)
> once they are scheduled. They are **not** architecture-review work and carry no `Fn` finding.
> Under **D-004** these build in stage **S3** (build the functional product), ahead of the S5 security sweep.
> An epic keeps its roadmap number, so this section is intentionally non-contiguous.

## EP38 — Employee Lifecycle Workflows  —  ⬜ Planned
**ID:** KAN-183 · **Label:** `lifecycle` `hr-process` `onboarding` `offboarding` `gdpr` `stage-S3`
**Source:** roadmap **BG4 — Complete the People-Ops Lifecycle**, epic EP38 (`EP38-S1`…`S4`).
**Description:** Make the portal handle the whole employment lifecycle — **join → transfer → offboard →
rehire** — not just registration and position change. Charter §1 lists these as lifecycle events the data
model must handle correctly; today the product can *create* an employee and *move* one, but has no
first-class onboarding, offboarding, transfer or rehire workflow.

> **Detailed acceptance criteria, edge cases and the GDPR retention/erasure rules live in
> [`../product-team/deliverables/EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`](../product-team/deliverables/EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md)**
> (Business Analyst — in authoring). The criteria in the table below are the **backlog-level summary** and are
> deliberately shorter; where the two differ, the BA's file is authoritative for detail and this table for scope.

> **Build order (roadmap §E, S3):** **KAN-184 → KAN-185 → KAN-183**. Offboarding is the Must and closes a real
> compliance gap; transfer reuses an engine that already exists; onboarding is the largest new surface.
> **KAN-186 (rehire) is "Later"** in the roadmap and is **not in this cycle** — it is listed here for traceability,
> not for scheduling. Do not start it without an explicit SPM decision.

**Dependencies — these gate delivery, they are not advisories:**

| # | Dependency | Gates | Why it is real |
|---|---|---|---|
| D1 | **KAN-155** — atomic writes / `transaction()` context manager (EP29, S2 enabler) | **KAN-184, KAN-185** — hard prerequisite | Both close out multi-table units of work (status + exit date + user deactivation + checklist close; or org assignment swap + manager re-point). Without a single commit/rollback boundary, a mid-sequence failure leaves a half-offboarded employee — access revoked but still ACTIVE, or moved but with no manager. **Do not start KAN-184/KAN-185 before KAN-155 lands.** |
| D2 | **KAN-166** — migration tool with version tracking (EP31, S2 enabler) | **KAN-183, KAN-184** | Both add new tables (checklist templates/tasks, offboarding cases). The `org_change_*` tables already exist only in migration 06 and not in the baseline — that drift is the exact failure KAN-166 exists to stop, and two more table sets make it worse. |
| D3 | **There is no audit infrastructure in the schema today.** `database/schema.sql` has 46 tables and **not one audit table**; the only decision trail is `org_change_approvals`, which is per-step state for that one workflow, not a general audit log. | **KAN-184** | The roadmap's "full audit entry" for offboarding is therefore a **new subsystem** — a table, a write path, a retention policy and a read surface — **not a column added to `employees`**. It is currently unestimated and unowned. **Needs an SPM/Architect decision before KAN-184 is Ready** (see Open items). |
| D4 | `employees.employment_status` and `employees.exit_date` **already exist** (`database/schema.sql`, `employment_status` constrained to ACTIVE/INACTIVE/RESIGNED/TERMINATED) — but **no route writes either one.** `exit_date` appears nowhere in `app/`; the only `UPDATE employees` in the codebase sets `gender`. | **KAN-184** | Offboarding will be the **first** code ever to produce a non-ACTIVE employee. Every `WHERE employment_status='ACTIVE'` filter across dashboard, directory, org tree, search index, notifications and manager resolution is consequently **untested against real non-ACTIVE rows**. Treat "what disappears, and what must not" as in-scope test work, including an offboarded **manager** whose reports would otherwise dangle. |
| D5 | `users.is_active` exists and is toggled manually from the admin panel | **KAN-184** | Half of "revoke portal access" exists, but as an unrelated manual action. KAN-184 must drive it from the workflow rather than rely on an admin remembering. |

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-187 | As a **compliance owner**, I want one immutable, company-scoped audit trail so any change to a person's record can be explained after the fact. (D3 — platform capability, prerequisite for KAN-184) | `audit_log` table + `app/services/audit_service.py`; append-only enforced by a DB trigger on UPDATE (DELETE deliberately left open for retention purge — TD-13); JSONB **field-level diffs only, never whole rows**; subject recorded as employee id + employee number, **never name**, so a row survives erasure; mandatory non-null `company_id` taken from the affected entity; closed action enumeration; mandatory reason; correlation id grouping one unit of work; outcome + error code; `retention_class`. `record()` joins the **caller's** open `transaction()` (KAN-155) and never opens its own — the audit row commits with the change and vanishes with a rollback. Reversible migration `08_audit_log(_down).sql` + regenerated `schema.sql`; `audit_log` feature code with read-only defaults for PORTAL_ADMIN + HR_ADMIN. | Must Have · P1 — ✅ **Done** (read UI is Wave 3, not this story) |
| ⬜ KAN-183 | As **HR**, I want an onboarding checklist workflow for a new hire so nothing is missed before day one. (EP38-S1) | Company-configurable task template (task, assignee by role or named person, due date relative to `join_date`); a checklist is instantiated when an employee is registered, and links back to that employee; each task carries status + who completed it and when; HR can see outstanding tasks per new hire and across the company before day one; new tables (KAN-166); company-scoped and gated by `@require_feature_access`. | Should Have · P2 |
| ⬜ KAN-184 | As **HR**, I want an offboarding workflow (access removal, exit date, asset return) so departures are clean and auditable. (EP38-S2) | Offboarding case sets `employees.employment_status` (RESIGNED/TERMINATED) **and** `exit_date`, and deactivates the portal user (`users.is_active=false`) — no route writes any of these today; asset-return / access-removal checklist completed before the case can close; the whole close-out is **one atomic write** (KAN-155); every step written to an **audit trail that does not exist yet** (D3); company-scoped and gated by `@require_feature_access` per `CLAUDE.md`; non-ACTIVE employees verified to drop out of directory, dashboard, org tree, search and manager resolution — reports of an offboarded manager must not be orphaned; GDPR retention/erasure per the BA's criteria file. | Must Have · P2 |
| ✅ KAN-185 | As a **manager/HR**, I want a transfer flow (BU / functional unit / location / manager) reusing the org-change engine so moves are consistent. (EP38-S3) | Transfers are raised as `org_change` requests and run through the **existing sequential multi-level approval engine** (`app/services/org_change_service.py`) — reused, not re-implemented; **no bypass path**; the KAN-139 rule stands (an employee can never initiate their own move); nothing is applied until the final level approves and any rejection applies nothing; company-scoped; the apply step is atomic (KAN-155). | Should Have · P2 — 🟡 **In progress**. **Done:** the shared *Request Position Change* dialog extracted to `templates/org_change/_move_modal.html` (one component, one endpoint, one engine — no second write path); submission guards on the single creation path (no-op move, pending-move conflict, non-ACTIVE subject or manager, reporting cycle, cross-tenant unit/manager UUIDs); prefill now returns the approval chain, the "Currently:" placement and the direct-report count; **both entry points wired** — employee profile and the directory row `⋯` menu — plus the org-tree legend's keyboard-equivalent line (WCAG 2.1.1 / 2.5.7). Evidence: pytest 4,636 · browser 93/93 · vacation 39/39 · `tests/test_transfer_entry_point.py` (59). Delivery also uncovered and fixed **D-185-1**, a live data-loss defect in `_apply_change` (see below). **`AC-185-07` effective-dating is now DELIVERED by KAN-189 (10 Aug 2026)** — the dialog carries a required, bounded **Takes effect on** date defaulting to today, `org_change_requests.effective_date` persists it, and one date drives both ends of the placement boundary. **CFL-4 is closed with no history rewritten** (ADR-020, half-open intervals). **KAN-185 has no outstanding acceptance criteria and is ready to close** pending the UAT lead's sign-off. |
| ⬜ KAN-186 | As **HR**, I want rehire to restore/relink a prior employee record so history isn't lost. (EP38-S4) | Registration detects an existing prior record for the same person and offers relink instead of creating a duplicate; the record is re-activated with a **new employment period distinguishable from the old** (prior `exit_date` preserved, not overwritten); prior org, manager, skills and certification history retained; the audit trail spans both periods. | Could Have · P3 — ⏸ **Later** (roadmap §E "Later"; **not this cycle**) |

**Defects found and fixed during EP38 delivery:**

| # | Defect | Found by | Fix |
|---|---|---|---|
| D-185-1 | **Data loss on apply.** `_apply_change()` inserted the raw proposal, and a request stores only the fields that changed. Approving a business-unit-only move therefore **silently erased the employee's location and functional unit**. Pre-existing on the drag-and-drop path, but latent there because the drop prefilled every field; KAN-185's "— No change —" defaults made partial proposals routine and turned it into a probable failure. | Driving the **approval chain** in a browser — not by any test. All 4,628 tests passed with the bug present, because every existing apply test passed a fully-populated proposal. | The new assignment row is now the outgoing row **overlaid** with what changed (`app/services/org_change_service.py`). Regression coverage: `TestApplyCarriesUnchangedFieldsForward` — BU-only, location-only, manager-only, full proposal, and no-prior-assignment. |
| DEF-001 | **An approval nobody could find.** A position change awaiting your decision never reached the notification bell's approvals area — `loadBellList()` fetched `/api/vacation/team-pending` only, and the badge counted vacation only. The bell displayed **"No pending approvals ✓" while an approval was waiting**, and the request appeared only as read-only text in *My Notifications*. `/api/org-change/pending-count` had existed since EP27 with **zero callers** — the plumbing was built and never connected. | The **stakeholder**, during a live demo, asking why the bell showed nothing. Not by any test: UAT asserted the bell opened, never what was in it. | Bell now counts and lists position changes in their own **Position Changes** section, feature-gated (`has_feature_access('org_change')`), with **✓ Approve** as a quick action and **✗ Reject** deep-linking to `/org-change?review=<id>&action=reject` so a reason is recorded. UAT §18 covers badge, listing, controls and deep link. |
| DEF-002 | **Every notification rendered as a rejection.** The bell's icon was `event_type === 'VACATION_APPROVED' ? '✅' : '❌'` — one event got a tick and **every other event on the system got a red ❌**, including "was fully approved and applied" and requests not yet decided. The notification card was also success-green for all events. | The **stakeholder**, live: *"why do I see a cross before I have decided?"* | Explicit `NOTIF_ICON` map keyed by event type — decided outcomes ✅/❌/🚫, in-flight ⏳, receipts 📨, unknown falls back to a neutral 🔔 **never to ❌**. Card background neutralised. New `ORG_CHANGE_SUBMITTED` event separates the requester's receipt from the approvers' call to action. UAT §18 asserts ⏳ on an undecided request and ❌ on a real rejection. |
| DEF-003 | **Dead calls to action never left the bell.** "Awaiting your approval" survived after the request was decided, for every approver who had not personally acted — `user_notifications` had no link back to the entity, so nothing could retire it. | Same demo session, reviewing the bell across four roles. | Migration `09_notification_related_entity.sql` adds `related_type` / `related_id` (+ partial index); `notification_service.resolve_related()` retires the call to action on **reject, level advance, final approval and cancel**, before the next announcement so it cannot sweep away the notification it just wrote. Covered by three engine tests and UAT §18. |

| DEF-004 | **CI red: `audit_log` missing from `portal_features`.** Migration `08_audit_log.sql` §3 registers the feature with an INSERT, but a fresh database is built from `schema.sql` (structure only) + `seed_rbac.sql` and **migrations are never replayed**. The row is data, so the schema dump could not carry it and nobody added it to the seed — CI's database had the audit_log TABLE but no audit_log FEATURE. Every developer machine passed because migration 08 had been applied there by hand. | GitHub Actions, run 31299506684 — 1 failed / 4,635 passed. Not reproducible locally against the dev DB, which is exactly the trap. | `audit_log` + its read-only PORTAL_ADMIN/HR_ADMIN grants added to `database/seed_rbac.sql` as `INSERT…SELECT` keyed on role name (so per-company roles are covered and it cannot drift from the role list). Guard: `TestFeatureRegistryHasNoDrift` in `tests/test_regression.py` compares every feature a migration registers against a fresh build and names the culprit migration — verified to fail on this exact defect before being accepted. `CLAUDE.md` "Adding a new feature" now lists **four** places, not two, plus the throwaway-DB command that reproduces CI locally. |

**Demo Readiness Gate record — DEF-001/2/3 fix — 9 Aug 2026** (first run of
[`DEMO_READINESS_GATE.md`](DEMO_READINESS_GATE.md)):

```
Demo scope     : bell carries position-change approvals; approval AND rejection paths
Data / env     : seeded dev DB, localhost:8000, Chromium
                 concurrent writers: YES — one unrelated PENDING request (Siim Kallas,
                 raised by Mihkel Kask 09:04) from another session. Uncontended subjects
                 chosen (Marek Pärn, Joana Cruz) and the stray request named aloud up front.
D1 Story truth        : BA — DEF-001/2/3 each mapped to a demo step
D2 Every actor        : UAT — requester, level 1, level 2, a second level-1 approver who
                        never acts, and the subject
D3 Both outcomes      : UAT — Part A approved end to end + applied; Part B rejected from the
                        bell, state proven unchanged after
D4 Feedback surfaces  : UX — 10/10 blind-spot list; badge, actionable item, icons,
                        retirement, subject, requester, other approver, deep link
D5 Access & tenancy   : Architect — bell section gated by has_feature_access('org_change');
                        /api/org-change/pending is company-scoped and per-step filtered
D6 State & rehearsal  : Delivery — rehearsed headless twice, both 18/18; re-runnable
                        (target unit chosen at run time, never hardcoded)
D7 Automated evidence : UAT — pytest 4,636 · browser 93/93 · vacation 39/39; new UAT §18
                        asserts bell CONTENT, and 3 engine tests assert the retire ordering
D8 Documentation      : owners — TECHNICAL_DOCUMENTATION §19.1/19.1a, CLAUDE.md, charter,
                        persona files, this backlog, all in the same commit
D9 Demo script        : SPM — scratchpad bell_flow.py, narrated
Known defects carried into the demo: none. Open policy question (item 5 below) stated, not fixed.
VERDICT (SPM): GO — live run 18/18
```

> **Process note:** DEF-001/2/3 were all found by the stakeholder during a demo, with pytest, the browser
> suite and the vacation suite **all green**. The engine was correct; the surface a user needs to *find*
> the work was neither built nor asserted. That is what produced
> [`DEMO_READINESS_GATE.md`](DEMO_READINESS_GATE.md) — in particular **D4**, the feedback-surface
> blind-spot list, and **D7**, which now requires that the suites actually assert the behaviour being
> demoed rather than merely passing. This is also the third and fourth KAN-185 defect found only by
> driving a real browser (the earlier two: the `_apply_change` data loss above, and an HTML-escaped
> `onclick` that rendered a dead button while a substring assertion passed).

**Open items for the product owner / SPM (recorded, not resolved here):**

1. ~~**The audit subsystem (D3) has no epic, no story and no owner.**~~ **Resolved:** tracked as **KAN-187**,
   a platform capability sequenced **ahead of** KAN-184 (per the Architect's ADR-009 and his §12 recommendation
   that it be its own story so EP35/EP39 do not each invent an audit trail). Delivered — table, service,
   reversible migration and tests. The **read surface / audit viewer is deliberately not in KAN-187**; it is
   Wave 3 work and still needs an SPM decision (OQ-1: per-employee timeline on the profile, a company-wide
   viewer, or both).
2. **The roadmap does not say what "asset return" is** (EP38-S2). There is no asset or equipment entity in the
   schema. Either it is a free-text checklist item under KAN-183/184, or it is an asset register — a materially
   larger scope. BA to pin down; SPM to confirm the smaller reading.
3. ~~**"Promote" appears in the EP38 epic title in the roadmap but has no story.**~~ **CLOSED 2026-08-09 (SPM,
   EP42 Wave 3).** Promotion is **not** a KAN-185 transfer variant. It is **KAN-197 in EP42** — a first-class
   request type on the same org-change engine, proposing a new (family, level, step) and carrying a salary
   review that cannot be silently skipped. Note the type is named **`LEVEL_CHANGE`**, not `PROMOTION`, with a
   stored `direction` of UP/DOWN/LATERAL — see EP42 §12 Ruling 8: downward and sideways level moves are
   permitted, and labelling a demotion "Promotion" in the inbox, the bell and the audit trail was a defect
   waiting to be shipped. "Promotion" remains the word shown to users when the direction is UP.
   This also closes **EP38 OQ-1** and **EP38 CFL-7**.
4. ~~**Transfer vs. the existing position-change flow (EP27) needs a boundary.**~~ **CLOSED 2026-08-09 (SPM,
   EP42 Wave 3).** The boundary is: **one modal, one endpoint, one engine, three entry points** (org-tree drop,
   employee profile, directory row `⋯`). The shared `templates/org_change/_move_modal.html` extracted under
   KAN-185 is the single surface; EP42 adds the compensation and job-level blocks to it. The **request type is
   inferred from what the user changed** — placement only → `TRANSFER`; level changed → `LEVEL_CHANGE`; pay
   only → `COMPENSATION_REVIEW`. Drag-and-drop is therefore not a second way to do the same thing, it is a
   third way to open the same thing. See EP42 §4.4.6 (D4f).
5. **Segregation of duties: one person can satisfy every level of a multi-level chain.** ⚠ **ANSWERED
   2026-08-09 (SPM, EP42 Wave 3) — option (a) for money, option (b) for placement.** Carried as **KAN-198**
   (chain rules) and **KAN-203** (identity rules). Awaiting the product owner's ratification as **OQ-9**; the
   team builds against the answer meanwhile. The original framing is kept below because the reasoning still
   applies, and because Wave 2 found the problem is **larger than this item described** — see the two Critical
   defects **DEF-42-4** and **DEF-42-5** in the EP42 section: today an HR_ADMIN can raise a position change
   **for themselves** and **approve it**, on the seeded default chain, which is not "overlapping approvers the
   company may have meant to configure". Original framing — **needs a product
   decision — not a defect until it has one.** In the seeded Acme Corp configuration, level 1 is the
   `HR_ADMIN` *role* and level 2 is a *named* approver who also holds `HR_ADMIN`. Nothing in
   `org_change_service.decide()` prevents the same user deciding level 1 and then level 2, so a chain the
   company configured as two-level control operates as one-person control. Observed live on 9 Aug 2026: the
   level-2 approver received the level-1 "awaiting your approval" notification, correctly, because she holds
   the role. The options, for the SPM/business to choose between:
   **(a)** block a user from deciding more than one level of the same request (a hard rule in the engine);
   **(b)** warn but allow, and record it in the audit trail (KAN-187) as a self-approval;
   **(c)** accept it as configuration — the company chose overlapping approvers and may have meant to.
   Note this is a **control** question, not a UI one; whichever way it goes, the approval chain admin page
   should show the overlap when a company configures it. Also relevant to KAN-184 offboarding.

---

## EP42 — Compensation, Job Architecture & Pay Equity  —  ⬜ Planned
**ID:** KAN-188 · **Label:** `compensation` `job-architecture` `pay-equity` `gdpr` `multi-tenant` `stage-S2` `stage-S3`
**Source:** the product owner's request of 2026-08-09, decomposed as **R1–R7**. Roadmap business goal **BG7 —
Pay decisions this company can defend** (new; see the roadmap §C and §D).
**Description:** Give the product a governed compensation record, a per-tenant job-levelling framework, and a
pay-equity check — and couple pay to the two workflows the product already owns end to end. Today the product
holds **no** compensation data of any kind (no salary, pay, grade, band, level or currency column, table, route,
service or template anywhere), and `employees.job_title` is free text with no catalogue behind it. Every pay
decision the product's users make is therefore made off-system, which is the largest single off-system
intervention left in the people-ops surface and sits inside two workflows the portal already runs.

> **The authoritative detail lives in four deliverables. This section is the backlog-level summary; where they
> differ, they are authoritative for detail and this table for scope and sequencing.**
>
> | Document | Owner | What it holds |
> |---|---|---|
> | [`../product-team/deliverables/EP42_SPM_SCOPE_AND_DECISIONS.md`](../product-team/deliverables/EP42_SPM_SCOPE_AND_DECISIONS.md) | SPM | Epic definition, scope in/out/later, **decisions D1–D8**, the **Wave-3 reconciliation and every conflict ruling (§12)**, risks, open questions, tasking |
> | [`../product-team/deliverables/EP42_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`](../product-team/deliverables/EP42_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md) | Business Analyst | **532 numbered acceptance criteria** (`AC-<story>-<nn>`), business rules BR-1…BR-8, the GDPR resolution for pay data, traceability |
> | [`../product-team/deliverables/EP42_TECHNICAL_DESIGN.md`](../product-team/deliverables/EP42_TECHNICAL_DESIGN.md) | Senior Architect | **ADR-014 … ADR-023**, 14 new tables, migrations, service/API design, **112 engineer-level tasks** with estimates |
> | [`../product-team/deliverables/EP42_UX_SPEC.md`](../product-team/deliverables/EP42_UX_SPEC.md) | UX / Product Designer | Every screen, state, copy string, validation message and accessibility annotation; the ten discretion rules |
> | [`../product-team/deliverables/EP42_UAT_TEST_PLAN.md`](../product-team/deliverables/EP42_UAT_TEST_PLAN.md) | UAT Lead | **300 test cases**, the **21-attack confidentiality catalogue**, 12 hand-computed arithmetic fixtures, the Demo Gate pack |

**Why R6 (job levels) is a prerequisite of R5 (pay equity), measured rather than asserted:** in the seeded data
Acme Corp has **46 employees across 41 distinct free-text job titles**, of which exactly **one** title has three
or more people in it; Telia has **100 across 75**, with six. Grouping a "same position" comparison on `job_title`
produces comparison groups of size one. The job ladder is what supplies the grouping key.

> **⚠ AMENDMENT A1 — 2026-08-09 — the product owner has answered, and it changes W4.** Full re-ruling in
> `EP42_SPM_SCOPE_AND_DECISIONS.md` §14. The two things anyone reading this table must know:
>
> - **OQ-1 CONFIRMED — progression is not automatic.** But the model is richer than specified: **every step
>   carries its own defined responsibilities and expectations**, **the manager authors the next step as a
>   forward-looking roadmap for that specific employee** (its purpose is transparency, so the employee must be
>   able to see it), and **step counts are configured per level per company** with no global default. An
>   employee **enters a level at step `.0`**, not `.1`.
> - **OQ-3 REINTERPRETED — "5%" is not a pay-equity threshold. It is the pay increment between consecutive
>   steps**, company-defined, because taking on additional responsibility must be matched by a pay adjustment.
>   The reference value therefore stops being the **group median** and becomes the **step's configured pay
>   point**. **The `n ≥ 3` minimum and the 80% coverage gate are withdrawn for the primary check** — one
>   employee can be compared against their own step's value — which dissolves the thin-data problem (46
>   employees, 41 titles, one title with n≥3). **The statistical machinery survives intact for the gender-gap
>   check, which still needs group sizes.** R5's original ask is still satisfied: two people at the same step
>   are measured against the same point, so a gap between them still surfaces.
>
> **Three new stories (KAN-206, KAN-207, KAN-208), a fourth feature code (`job_architecture`), and one boundary
> stated plainly: EP42 records that a step change happened at a review; it does not build the review.**

> **⚠ WAVE-5 RECONCILIATION — 2026-08-09 — two rulings change this table.** Full detail in
> `EP42_SPM_SCOPE_AND_DECISIONS.md` §16.
>
> - **The nearest-step rule (§16.2) replaces the tolerance as the finding boundary.** UAT proved that because the
>   tolerance had to be *strictly less* than half the increment, **a perfectly fitted ladder still flagged ~20% of
>   the workforce** — 4 findings from 10 correctly-fitted employees. A finding is now raised when **the
>   employee's pay is nearer to a *different* step's pay point than to their own**; the dead zone becomes **zero
>   by construction** and a fitted backfill raises **no findings on day one**. The tolerance survives only as a
>   non-notifying quality measure. This dissolves four Wave-4 conflicts and **deletes work from three
>   specialists**.
> - **The build order had a defect and it was mine (CFL-42-41).** KAN-191's fitted-step backfill fits by
>   comparing pay to KAN-206's pay points — and fitting needs **pay data** too. The fitting half is now
>   **KAN-209, at the end of W2**. **Ordering invariant: the ladder-fitted-and-reviewed gate ships CLOSED with
>   KAN-206 and is opened only by KAN-209's review.** Between pay points existing and steps being fitted,
>   everyone sits at `.0`; the closed gate is the only thing that makes that window safe.

> **⚠ AMENDMENT A2 — 2026-08-09.** Full re-ruling in `EP42_SPM_SCOPE_AND_DECISIONS.md` §18. Four things:
> **OQ-5 CLOSED — base salary only** (his words "at this point" convert it into an extensibility rule, not a
> deletion) · **the job-family model is CONFIRMED unchanged** — his worked example maps onto `job_families` →
> `job_levels` exactly, so no positions table and no rebuild · **the job level may be hidden from the employee
> per company policy**, which constrains the transparency surfaces UX built in Wave 4 (**CFL-42-55**) · and a
> **new capability: an annual hike cycle**, which is **NOT in EP42** — see below.
>
> **The hike cycle goes to a sibling epic, EP43.** EP42 is already 23 stories and ~14–16 weeks and has been
> amended twice in a day; a recurring annual business process with a performance input would take it past the
> size defensible as one commitment, and it is a different shape of thing (a process, not a data model).
> **But the half that protects EP42's own integrity stays inside EP42** as **KAN-210** plus effective-dated pay
> points in KAN-206: without re-basing, an ordinary annual hike **flags the entire workforce in the first
> cycle** — checked, and note this **corrects A2's own premise that the failure is "silent" (CFL-42-54)**: with
> a 5% increment, any hike above **2.5%** puts every employee nearer the *next* step's pay point than their own
> (a 4% hike sits 4.00% from their own point and 0.95% from the next). Loud, not silent — which makes re-basing
> more urgent and is a point in favour of the nearest-step rule.

> **⚠⚠ AMENDMENTS A4, A5 and A6 — 2026-08-09 — THE OWNER OVERTURNED THE EPIC'S CENTRAL MECHANISM.**
> Full re-ruling in `EP42_SPM_SCOPE_AND_DECISIONS.md` §22. **Read §22.0 before any story below.**
>
> **The corrected model, and it only runs one way:**
>
> ```
>        job content & responsibility  →  STEP  →  BASE PAY
>        BASE PAY  →  STEP                                    ⛔ FORBIDDEN
> ```
>
> A step is an assignment about **what work someone does**, made by a human at a review. The step has a defined
> value and an employee's base pay **is** that value × FTE. **The system must never propose, infer, imply,
> suggest, pre-select or "fit" a step from a salary figure** — not in the backfill, not in an import, not as a
> default, not in a tooltip. His words: *"that does not mean he will be assigned to 2.4 or 2.3 just to match
> the salary."*
>
> **What that kills.** The **nearest-step rule** (Wave-5 §16.2) is **withdrawn in full — as a mechanism and as
> a description**: *"paid closer to step 2.2"* is a claim about somebody's step and standing rule 6 forbids it.
> A deviation is now stated as a **magnitude against their own step** ("base is €2,430 / 4.8% below the value
> of step 2.4"). The **tolerance** is gone; a **materiality threshold (default 1%) governs notification only
> and never suppresses a computed number**. **KAN-209's step-fitting backfill is forbidden and repurposed.**
>
> **What that creates — `additional pay` (KAN-218, new).** Base and additional are two distinct,
> separately-governed amounts. Tom is about to resign, local HR grants 5%: **Tom stays at step 2.1, base stays
> €51,000 — the step's value — and €2,550 is recorded as additional pay with a reason.** He is not "a 2.2 now".
> The correspondence check compares base to the step's value and raises **nothing**. Mandatory reason code,
> effective-dated, optional end date or a mandatory review date, approved through the chain with four-eyes,
> **never in an `audit_log` diff**. Excluded from the correspondence check; included in Check B.
>
> **The hike rate is per step-transition, per year, set by Global HR** — *"from 2.0 to 2.1 the hike will be 2%
> this year while from 2.1 to 2.2 it will be 2.4"*. So `step_increment_pct` on the **level** is the wrong
> shape: the rate lives on the **transition** and is **year-scoped with history**, and
> `job_step_increment_overrides` stops being an exception path and becomes the schedule itself. Compounding
> survives and generalises — 2.0 = €50,000 → 2.1 = €51,000 → 2.2 = **€52,224** (linear would give €52,200).
>
> **The re-basing question asked three times is DEAD, not deferred.** It assumed an across-the-board hike that
> moves salaries independently of the ladder, and it assumed base and the step's value can drift apart. Under
> A6 neither is true — **moving the ladder and paying people are the same act**, which *promotes* KAN-210 from
> a maintenance action to the mechanism by which a company grants a rise. What survives is one narrower, new
> question: **does the entry value of a level move each year?** — put to him as Q1 in §22.13, with numbers.
>
> **Two authorities, one HR role** — *"Global HR department decided…"* / *"the local HR department decides…"*.
> **A fifth feature code, `pay_policy`** (registered in KAN-199) separates them: Global HR authors the ladder's
> economics (entry values, the rate schedule, pay markets, the threshold, the re-base); local HR acts on one
> person's pay. **CFL-42-20's thresholds move from `company_settings:w` to `pay_policy:w`** — the ruling that
> it must not be a role check is preserved, only the home changes, and UX gets one gate per screen instead of
> two. Organisational scoping (HR-for-the-Nordics) is **not** being built on this evidence — Q2 to the owner.
>
> **Advise, do not block** (A4 §2, his principle) is adopted as a standing rule **with an explicit boundary**:
> judgements about an **amount** are advisory and overridable; **integrity controls are not**, and the
> Category 2 list — KAN-203's subject≠initiator and subject≠decider, KAN-198's initiator≠approver,
> approver≠approver, ≥2 satisfiable levels, and no SYSTEM_ADMIN bypass — **is closed and may not be eroded by
> citing A4-1, because A4-1 is about amounts and says nothing about actors** (§22.7.1). Every override carries
> a recorded actor, a mandatory reason **code**, an audit row with no amount in it, and **visibility to the
> approval chain at decision time**. Override rates are reported with a 40% configuration-review tripwire.
>
> **Full performance management is confirmed** (A4 §4, A5 §2 — *"go ahead with full implemenation cycle as
> Product owneer accepting the delay"*). **§14.5 is recorded as SUPERSEDED BY OWNER DECISION**, not dropped —
> it stopped performance management arriving by accident and did not stop him choosing it on purpose. **EP44
> is entered as a real epic of 22 stories, between EP42 and EP43.** **The step-disclosure switch is CLOSED**
> (A5 §1): per company, governing the **step**, defaulting to visible.
>
> **⚠ The challenge pass (§22.1) found two more team premises that were never his**, and both are acted on:
> **Check B (the gender pay-gap check) has no owner requirement behind it** — it came from the SPM's own
> reading of the EU Pay Transparency Directive, labelled *Assumption / Medium* at the time, and OQ-3 was
> marked "closed" by an answer to a different question. It is kept, re-labelled a **team** requirement,
> **descoped to a separable conditional slice**, and put to him (Q4). **KAN-208 comes out of W0** with it,
> which also takes R-19 (the vacation-eligibility side effect) off the critical path. And **A2-1's
> per-employee hike percentage is withdrawn as wrong** — "for each" means each step transition — which
> collapses most of EP43.

> **Build order — five waves, 23 stories. W0 is stage S2 (with the enabler set); W1–W4 are stage S3.**
>
> ```
> S2  KAN-203 ─┐                                    P0 — Critical defect, no EP42 dependency
>     KAN-204 ─┤ parallel                           EP33 debt, gates the first EP42 screen
>     KAN-188 ─┤                                    tenant switch + non-session resolver
>     KAN-189 ─┘ (second track, unblocks KAN-185)   effective dating
> S3  KAN-190 → KAN-191 → KAN-207                   ladder + expectations, level AND STEP ASSESSMENT,
>                                                   the roadmap — still no money anywhere in W1
>     KAN-199 → KAN-206 → KAN-210 → KAN-193 → KAN-194 → KAN-218 → KAN-195 → KAN-209
>                                                   markets + pay_policy, the per-transition rate schedule,
>                                                   ladder re-basing, the record, visibility, ADDITIONAL PAY,
>                                                   backfill, then RECONCILE base to the ladder and open the gate
>     KAN-196 → KAN-197 → KAN-198 → KAN-192         pay in the flow, level change, four-eyes, progression
>     KAN-200 → KAN-201 → KAN-202                   engine, delivery, history
>     ⬜ conditional on the owner confirming Check B:  KAN-208 + Check B inside KAN-200/201
> ```
>
> **CFL-42-41 — the build-order defect I shipped in Wave 4 — is CLOSED by A6 rather than worked around.**
> Step fitting had to sit in W2 because it needed pay points *and* pay data. **Job-based step assessment needs
> neither**, so it moves back into KAN-191 in W1, and KAN-209 becomes the pay reconciliation at the end of W2.
>
> **W1 now ends with a complete, shippable job-architecture slice with no compensation data in it at all** — a
> ladder, described expectations, everyone placed on a step, and every employee able to read what their next
> step requires. That is real value visible before any pay question is settled. **W2 remains the minimum
> shippable slice for the epic as a whole.**
>
> **KAN-194 ships in the same release as KAN-193 — not later.** A compensation record that exists for even one
> release without an enforced visibility model is a Critical defect the moment it exists; UAT has pre-declared
> that it will raise it as one.
> **W2 is the minimum shippable slice.** If the epic has to stop, it stops there with pay in the product,
> visible to the right people, backfilled.
> **W4 does not open until KAN-168 (real-DB test tier) has landed.** If KAN-168 slips, W4 slips — shipping an
> equity engine certified against mocks is not an acceptable alternative.

**Dependencies — these gate delivery, they are not advisories:**

| # | Dependency | Gates | Status | Why it is real |
|---|---|---|---|---|
| D1 | **KAN-155** — `transaction()` atomic writes | KAN-189, 193, 195, 196, 197, 198, 201 | ✅ **Done** — corrected in Wave 3; the SPM's Wave 1 table said "planned" | A `LEVEL_CHANGE` apply writes the org assignment, the level/step, the compensation record and 3–4 audit rows. Level moved but pay not written is the worst state in this epic. **Nothing is waiting on this.** |
| D2 | **KAN-166** — versioned migrations | KAN-188, 189, 190, 193, 199, 200, 201 | ⬜ Planned (S2) | 14 new tables, 2 altered, 3 feature codes. `org_change_*` drift is exactly what this exists to stop. |
| D3 | **KAN-187** — audit trail | Every mutating story | ✅ Done | Reused, not re-invented. Needs `ACTIONS` extended and the money guard added (**CFL-42-2** / ADR-019) — and it must also gain the two codes **EP38 already needs and does not have**. |
| D4 | **KAN-168** — real-DB integration tier | **KAN-200 above all**, plus every criterion asserting final row state | ⬜ **Not started — this is the live scheduling problem** | Group formation, `percentile_cont`, coverage arithmetic and every exclusion constraint are SQL semantics. A DB-mocked suite proves we called `psycopg2`. **P0 for W4.** |
| D5 | **KAN-185** — transfer flow | **Not a dependency — the reverse.** KAN-189 resolved CFL-4 and unblocked `AC-185-07` with no history rewritten (ADR-020) | ✅ **Unblocked and complete** (10 Aug 2026) | **EP42 repaid EP38, exactly as planned.** KAN-189 ran on the second track and closed KAN-185's last open criterion. |
| D6 | **EP35-S2** — bulk import wizard | KAN-195 (soft) | ⬜ Planned (S3) | KAN-195 is written against the EP35-S2 contract; if it ships first it is refactored onto the wizard, never left as a parallel importer. |
| D7 | **KAN-163** — any scheduler | Periodic equity re-evaluation · automatic retention purge · time-based progression · future-dated placement | ⬜ **Not planned** | Why evaluation is event-driven + on-demand, why the retention purge is manual, why there is **no automatic level roll-up**, and why a future-dated *placement* is refused while a future-dated *pay* record is allowed. **Do not design around a scheduler that does not exist.** |
| D8 | **Backlog open item #1** — the audit read-surface decision | KAN-202 | ⬜ Unresolved (SPM) | KAN-202 is a **compensation** surface by design so it does not block, but the two must not be designed in ignorance of each other. |
| D9 | **DPO / legal validation** — 7 items (DPO-1…DPO-7 in the BA's §4.7.9) | **DPO-1** blocks Check B only; **DPO-2** blocks the retention class; the rest are launch | ⬜ Not started | Charter §9.7 — nothing here is legal advice. **DPO-1 is a purpose-limitation question**: `employees.gender` was collected for vacation eligibility and Check B reuses it. |
| D10 | **DEF-42-1** — the CSV importer cannot write a valid `employment_type` | KAN-195 quality, KAN-200's exclusions | ⬜ Raised against **EP21**, P1, fix in S2 | EP42 keys its exclusions and FTE handling on `employment_type` and bulk import is the only bulk path. Not absorbed into EP42 — see the defect table. |
| D11 | **EP28 / KAN-148** real authentication | Nothing in the build — **everything in the enforceability** of the visibility model | ⏸ Deferred to S5 (D-004) | The visibility model is a **correctness** control, not a security control, until KAN-148 lands. This is a Demo Readiness Gate disclosure, not a build blocker. |

**Stories.** Grouped by wave, in build order. Acceptance criteria here are the backlog-level summary; the BA's
file carries the numbered, individually testable criteria.

### W0 — platform enablers and two debts (stage **S2**) · *KAN-208 moved out by A6 — see the conditional slice*

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-203 | As a **compliance owner**, I want it to be impossible to raise or approve a request about myself, so nobody can be on both sides of their own move or their own pay. (Fixes **DEF-42-4** + **DEF-42-5**; closes the gap between `CLAUDE.md`'s headline invariant and the code) | **Subject ≠ initiator:** `_can_initiate_for` refuses when the subject is the initiator, for **every** request type and **every** role including HR_ADMIN, PORTAL_ADMIN and SYSTEM_ADMIN — the admin exemption exists so HR can move *other people*, and it has never been intended to cover acting on oneself. **Subject ≠ decider:** `decide()` refuses when the decider is `req['employee_id']`, at any level, for any role. Both refusals are specific, audited and covered by regression tests that fail without the guard. `CLAUDE.md`'s org-change invariant 2 is reworded in the same commit to say explicitly that **nobody**, including admins, may initiate or decide a request whose subject is themselves. **Universal — not money-scoped**; the initiator≠approver rule is money-scoped and lives in KAN-198. | **Must · P0** — Critical, pre-existing, exposed today |
| | **✅ DONE (10 Aug 2026).** Both guards refuse ahead of every exemption, audited as `ORG_CHANGE_SELF_ACTION_REFUSED` (`retention_class='SECURITY'`, `outcome='FAILED'`); the audit write is the one deliberate exception to ADR-009's join-the-caller's-transaction rule, because a refusal has no unit of work to join, and it can never turn a refusal into a 500. **T-203-3 went wider than the ticket scoped it:** the profile and directory already hid the affordance, but the org tree made *every* card draggable and — more seriously — `list_pending` and `_step_approver_user_ids` offered the subject a live **Approve/Reject** on their own move, in the inbox *and* the bell. That is the DEF-001/2/3 failure mode verbatim, so it was fixed here rather than logged: your own card is no longer draggable (it stays a **drop target** — moving somebody else under you is ordinary), the inbox omits requests about you, and the approver-resolution SQL excludes the subject so the badge count never includes it either. Named reproductions live in `tests/test_transfer_entry_point.py` §8 and were **verified failing (18 tests) with the guards removed**, not merely asserted green. `CLAUDE.md` invariant 2 + `docs/ARCHITECTURE_REVIEW.md` **F32** landed in the same commit. **4,660 pytest · browser 93/93 · vacation 39/39.** | |
| ✅ KAN-204 | As **any user**, I want the shared shell to give a visible focus ring, announce async changes and respect reduced motion, so every new screen is usable without inventing its own. (**EP33 debt**, delivered here because EP42 adds ~10 surfaces and cannot absorb it ten times) | Three shared additions to the shell: **A1** a global `:focus-visible` indicator (today only `.row-menu-btn` and `.row-menu-list > *` have one); **A3** shared live regions in `base.html` (today the only live region in the product is private to `_move_modal.html`); **A9** a `prefers-reduced-motion` block (today absent). EP42's coverage meters, progress bars and equity spinner all animate. **No EP42 screen starts before this lands.** Tagged EP33 so that epic's scope shrinks honestly rather than EP42 absorbing it invisibly. | **Must · P1** |
| | **✅ DONE (10 Aug 2026).** All three landed, and T-204-1's instruction to *verify* rather than assume earned its keep: the audit confirmed the story's premise exactly — two focus rings in the entire product, no reduced-motion support, and the only live regions private to the move dialog. **A1** is one `--focus-ring` token (with a lighter dark-theme value, because `#2563eb` on `#0f172a` is borderline against WCAG 1.4.11's 3:1) plus a global `:focus-visible` rule placed **last in the stylesheet on purpose** — it is 0,1,0, the same specificity as the three controls that set `outline: none`, so it wins by source order alone and moving it up the file silently breaks them. A test asserts that ordering and fails if a new `outline: none` is added after it. **A3** is one polite + one assertive region, first in `<body>` (a region injected with its text is not reliably announced) and `.sr-only` rather than `display:none` (which removes it from the a11y tree and silences it — the failure that looks like success); the move dialog was **migrated off** its private pair, and a grep-assert over `templates/` now fails the build if any screen declares its own. **A9** is a universal block using `.01ms`, not `0s`, because a zero duration fires no `transitionend` and code awaiting one hangs for ever; it caps the three **infinite** animations and leaves outline/colour cues alone. Also wired `announce()` into the directory's result count and empty state — a silent filter was a real gap, not a demo prop. Verified in a **real browser**, not only by asserting the CSS exists: 7 new checks prove the ring actually beats `outline: none` on the search box, that exactly one region pair is live, and that reduced motion applies in an engine honouring the query. **4,680 pytest · browser 100/100 · vacation 39/39.** Documented as `TECHNICAL_DOCUMENTATION.md` §8b so an EP42 screen calls the primitive instead of reinventing it. | |
| | **✅ KAN-189 DONE (10 Aug 2026).** All eight tasks. **ADR-020 is the story**: half-open `[from, to)` project-wide, so `effective_to` is the first day NOT covered. Read that way **CFL-4's "one-day overlap" was never in the data** — closing with `effective_to = D` and opening with `effective_from = D` is exactly adjacent — so the finding closed with **a stated convention and no history rewritten**, which is what the acceptance criteria asked for and the cheapest possible resolution. One date now drives both ends of the boundary, so they cannot drift apart. **Verified against real Postgres, not mocks**: `daterange(from, to, '[)') &&` reports **0** overlapping periods in `employee_org_assignments` and **0** among `SOLID_LINE` relationships. **DEF-42-2 closed**, and further than scoped — the code fix stops new NULL-ended reporting lines, and migration 10 also **repairs the 2 existing rows**, deriving each end date from its successor's `effective_from` (recovered from data that was always there, not invented) and leaving any row with no successor honestly NULL rather than guessed. `fmt_period()` / `fmt_last_day()` are the only sanctioned renderers, with a grep-assert against printing `effective_to` raw. **`AC-185-07` delivered → KAN-185 closes.** Verified CI-style on a throwaway database (`schema.sql` + `seed_rbac.sql`) so the column cannot be a dev-machine-only artefact. **4,718 pytest · browser 105/105 · vacation 39/39.** ⚠️ **Two honest gaps, both stated rather than implied: (1) per-company window values are NOT delivered** — they live on `company_compensation_settings`, a W1 table, and stubbing it early would make W1's own `CREATE TABLE IF NOT EXISTS` silently skip; `_dating_window()` is the single named seam. **(2) DEF-004a raised** — see the defect register. | |
| ✅ KAN-188 | As the **product owner**, I want to expose or hide a feature for one company without hiding it for another, and have that honoured everywhere, so I can package the product per tenant. (**R7** · D6) | `company_features.is_enabled` becomes a term in the **single central** resolution (`_load_feature_access`), one added `LEFT JOIN` on the query that already runs — effective access = **tenant switch AND role grant**. The default for an absent row is a **`portal_features.default_enabled` column**, not a Python constant. A **repair-then-materialise** migration: repair the 14 rows that are FALSE for features nothing consults (excluding `reports` and `skills_intelligence`, whose values are live), then materialise a row for every (company, feature) pair. **The acceptance criterion is a 330-cell before/after matrix** — 3 companies × 11 features × 10 roles resolve identically after the migration — captured as a fixture **before** any code changes. The off state is a real explanatory screen, never a 403 or a redirect. SYSTEM_ADMIN bypass preserved **and visibly signposted**. The two hand-rolled consumers are **deleted**, and a grep-assert test fails if `company_features` is read anywhere outside the resolver and the toggle route. **Also delivers `feature_access_for(user_id, company_id)`** — the non-session resolver KAN-196 needs (CFL-42-12), because this story is already rewriting that query. `enabled_for_hr` gains no consumer; removal path named (TD-17). Every toggle audited. | **Must · P1** |
| | **✅ KAN-188 DONE (10 Aug 2026).** Effective access is now `tenant switch AND role grant`, resolved by **one added `LEFT JOIN`** on the query `_load_feature_access()` already ran. The two hand-rolled tenant switches (`_analytics_enabled`, `_si_enabled`) are **deleted**, and a grep-assert fails the build if `company_features` is read outside the resolver and the toggle route. `feature_access_for(user_id, company_id)` delivered for KAN-196, deliberately uncached (it answers about somebody else). Every toggle audited as `COMPANY_FEATURE_ENABLED`/`DISABLED` (`SECURITY`), recording the transition, in one transaction with the write. The off state is a **real screen at 200** for a page and **403 JSON with `reason: tenant_feature_disabled`** for an API — and is shown **only** to a user whose role would otherwise allow the feature, because to anyone else it is untrue *and* leaks the tenant's licensing. SYSTEM_ADMIN bypasses the switch and the screen **says so**, so they cannot demo a feature the customer lacks. **The 330-cell matrix earned its place twice.** ⚠ **It caught one defect and, more usefully, revealed its own blind spot:** the snapshot measures the resolver, but the deleted gates lived *outside* it, so a blanket `default_enabled = TRUE` **silently granted `reports` and `skills_intelligence` to 'Sam Cpmapny'**, which had no row for either and was therefore already denied — while the matrix reported "identical". Fixed by defaulting the two licensed features **OFF** (the only two ever gated; "no row" historically meant denied) and comparing the old gates directly. Final state: **319 of 330 cells identical, 11 changed as designed** — all removals, at that one tenant, on those two features, with `SYSTEM_ADMIN` cells provably unmoved; the diff tool now enforces an explicit allow-list that permits removals only. ⚠ **Also walked into DEF-004 and caught it:** `default_enabled` is DATA, so setting it only in migration 11 left every **fresh CI database** defaulting both licensed features to TRUE while every developer machine read FALSE. Now in `seed_rbac.sql` too, guarded by `test_the_seed_and_the_migration_agree_on_every_default`. `enabled_for_hr` gains no consumer; removal path named in the route docstring (TD-17). **4,727 pytest · browser 105/105 · vacation 39/39**, plus a full CI-style rebuild from `schema.sql` + `seed_rbac.sql`. | |
| ✅ KAN-189 | As **HR**, I want a position change to carry the date it takes effect, so placement and pay move on the same day and history is not fudged. (D4d · **resolves CFL-4 · unblocks `AC-185-07` on KAN-185**) | `effective_date` on `org_change_requests` and `create_request()`; rendered in the shared move modal (deliberately absent today rather than silently discarded); `_apply_change` uses it as the boundary for closing the outgoing assignment and opening the incoming one. **Half-open `[from, to)` intervals adopted project-wide** (ADR-020), which closes CFL-4's one-day overlap **with no history rewritten**. After any applied change: exactly one current assignment, no overlapping day, asserted by direct DB query. Also fixes **DEF-42-2** — `_apply_change` closes `manager_relationships` rows with no `effective_to` and the dev DB holds 2 such rows; the pattern EP42 was told to copy is undated on the closing side. Back/forward-dating windows company-configurable; a future-dated **placement** stays refused (no scheduler), a future-dated **pay-only** request is allowed. | **Must · P1** |

### W1 — job architecture (stage **S3**) — R6 · **a complete slice with no compensation data in it**

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-190 | As a **customer admin**, I want to define my own job families, levels and steps — each step with its own responsibilities and expectations — so the ladder matches how we actually organise work and people can read what each step means. (**R6** · D3 · **A1**) | Company-scoped job **families**; ordinal **levels** within a family, each carrying **its own title**. **Steps run from `.0` (entry) upward**: a level's configured `step_count` is **the number of increments above entry**, so `step_count = 5` yields **six** discrete values `.0 … .5` — matching the owner's own `2.0 … 2.5` example. **Configured per level, per company, with no default** — Trainee→Junior and Junior→Mid are genuinely different distances; range 1–12 as a sanity bound, and the configurator requires an answer rather than defaulting one. **Each step carries an authored description of its responsibilities and expectations** (A1's largest addition) — readable by every employee, because that is its purpose. **Registers the fourth feature code `job_architecture` in all four places**: `r` seeded to **everyone** (an employee must be able to read their step and the next); **`w` seeded to `SOLID_LINE_MANAGER` (row-scoped to their direct reports), HR_ADMIN and PORTAL_ADMIN — it governs *roadmap authoring*, not the ladder.** **Ladder configuration itself is gated `org_structure:w`** — seeded HR_ADMIN + PORTAL_ADMIN, **no manager**, no seed change, precedent at `app/routes/org_change.py:381` (**CFL-42-35**, both halves: a manager must author roadmaps, and a manager must not edit the company's job architecture). The Feature Access tab's **label and description for `job_architecture` must say what it actually grants** — "read the job ladder; write step roadmaps for your reports" — or the grant misleads at the point it is made. A tenant that wants engineering managers to author the ladder **creates a role and grants `org_structure:w`**; the matrix already solves that and it needs no new code. Ladder **reads** move to `job_architecture:r`; **an employee's own level title on their profile or directory row stays `employee_profiles`**, so a tenant switching `job_architecture` off does not blank the directory (refines CFL-42-18). The level's **base pay point and step increment stay on `compensation:w`** — one screen, two gates, as ruled for Compensation Settings. A level's ordinal is **immutable once an assignment exists**; inserting a level mid-ladder has no path once occupied and the configurator says so **before** the ladder is built. Empty state never shows another company's or a global default's levels. **Save is publish** — no draft cycle, and the screen says so. **First-run asks whether the employee's own STEP is displayed to them** (**A2 §6**, corrected by **A3-4 / CFL-42-58**), default **on**, because he asked for level-expectation transparency twice and withholding is the exception a company invokes. **It governs the step, not the level** — in his own example the title *Junior Software Fullstack Engineer* **is** level 2 of that family, and he has said the title is always visible, so a switch claiming to hide the level would hide nothing while claiming to (standing rule 6: a label is a claim). Asking during setup means neither a silent policy breach nor a silently undelivered outcome. The prompt carries the honest sentence: **"Employees can still read the ladder and their own expectations, so this prevents display, not inference"** — the setting is labelled *do not display*, never *hide* (standing rule 6: a label is a claim). Per-step **"drafted by"** attribution and paste-friendly entry, because in most companies the content is written by engineering managers and transcribed by HR. **Nothing here can test whether the content is any good** — a ladder whose six steps all read "does more of what 1.1 does" passes every criterion in this epic and delivers none of the transparency the owner asked for (**CFL-42-47**, risk R-18), so *"the ladder reads as a real description of the work"* is now on the **Demo Readiness Gate's must-be-walked-by-a-human list**. Every change audited. **⚠ A4–A6:** the step expectations authored here are now the **only legitimate input to a step assessment** (KAN-191), so ladder-description completeness stops being a quality nicety and becomes a **hard dependency of the backfill** — **R-18 escalates to High × High**. The first-run prompt is unchanged and the step-disclosure switch is now **CLOSED** by A5 §1. | **Must · P1** |
| ⬜ KAN-191 | As **HR**, I want every existing employee placed on a **level**, so the ladder has people on it. (**R6** · R2 · D7 · **A1** · **re-scoped by CFL-42-41**) | Effective-dated assignment of an employee to a (family, level). A **mapping screen** listing every distinct free-text `job_title` with its headcount, assign a level per title, bulk-apply, plus a **CSV round-trip** — this screen decides whether the backfill finishes. **Step fitting is deliberately NOT in this story** — it moved to **KAN-209** in W2, because fitting a step to pay needs both KAN-206's pay points **and** actual pay data from KAN-193/195, and neither exists in W1 (**CFL-42-41** — the original build order would have run the fitted backfill a wave before the thing it fits against, producing exactly the `.0`-for-everyone alert storm the fitting exists to prevent). Everyone therefore defaults to step **`.0`** here, which is **harmless in W1**: Check A′ requires a configured pay point, none exists, so nothing is evaluable and no finding can be raised. `employees.job_title` **kept**, relabelled "Working title", never a grouping key; index and trigger untouched, the searchability consequence recorded as **TD-18**. **Level coverage** reported as a named figure with its denominator. **No algorithmic title→level suggestion in this cycle.** **⚠ A4–A6 — STEP ASSESSMENT MOVES HERE, and it does not come from pay.** A6 forbids deriving a step from a salary, so KAN-209's fitted-step backfill is withdrawn and replaced: **the subject's solid-line manager assesses each direct report against the step expectations authored in KAN-190.** **Nothing is pre-selected, nothing is suggested, and nothing may be derived from pay** — a pre-selection is a system claim about somebody's job content, and D4c's discipline (mandatory to answer, nothing pre-selected) applies to the one field A6 exists to protect. **`STEP_NOT_ASSESSED` is a distinct state and is NOT step `.0`** — the old "everyone defaults to `.0`" was itself a claim that a person is at entry level. An employee in it has **no derived base**, is **not evaluable**, renders as *"Step not yet assessed"* (never `2.0`, never a dash, never blank — D7's empty-state rule applied to steps), and is listed for assessment. HR override with a mandatory reason, plus a **completion meter**. **Distribute the work or it will not finish:** one HR person assessing 146 people is a project; forty managers assessing three or four each is a ten-minute task, and they are the only people who can do it correctly. **Design it in one sitting with KAN-207's roadmap authoring** — same person, same judgement. **This closes CFL-42-41** (the SPM's Wave-4 build-order defect) rather than working around it: job-based assessment needs neither pay points nor pay data, so it belongs in W1. **R-20 (new):** no criterion can test whether an assessment was done thoughtfully — held by the expectations shown at the point of choice, nothing pre-selected, HR's override, and a new Demo Gate human check, *"a manager can explain why this person is at this step"*. | **Must · P1** |
| ⬜ KAN-207 | As an **employee**, I want to read what my next step requires of me — written for me by my manager — so I know what I need to do next. As a **manager**, I want to author it. (**A1** — the object the owner actually asked for) | Distinct from KAN-190's generic step expectation: the expectation says *what step 1.2 means here*; the **roadmap** says *what you, specifically, need to do to get there*. **Authored** by the subject's solid-line manager — **who must be seeded `job_architecture:w`, row-scoped to their direct reports** (**CFL-42-35**: the fourth code was created so a manager could author a roadmap, and the seed as first written gave them no `w` at all, blocking this story outright) — or by any other `job_architecture:w` holder. **The employee is notified once, in-app, when a roadmap is written for them** (overruling the BA's and UX's "no": a roadmap the employee does not know exists delivers exactly zero transparency, and "it appears on their profile" assumes they visit their profile). No email; retires on view; contains no pay information. **Visible to the employee — not optional.** Transparency is the entire stated purpose; if the employee cannot see it, we have not built it. **"Mutually decided" is recorded, not enforced — and the label must not claim more than the mechanism delivers** (**CFL-42-50**): the button says **`Confirm we discussed this`, never *Accept***, and the displayed state is **`Discussed with Ravi on 14 March`, never "agreed"** — recording "agreed" when somebody merely read it is a false record about a person. An unacknowledged roadmap is still a live roadmap, nothing is blocked by non-acknowledgement, and it is surfaced back to the manager — **no blocking workflow for a conversation that happens in a room**, because a non-responsive employee must not be able to freeze their own development plan. **Versioned, not overwritten** — roadmaps are re-agreed at each review and "what did we agree in March" is the question this object exists to answer. **No ratings, no scores, no assessment of any kind** — it is a statement of expectations, and that boundary is what keeps it out of GDPR Art. 22 and EU AI Act territory. An employee sees **their own** roadmap and never a colleague's, asserted at the payload. **A disclosure-off rendering is required** (A2 §6, A3-4): where the company does not display steps, the employee still sees **their role, their job family and every level's expectations** — `/ladder` is confirmed as a main-nav surface and job family is an explicit part of what it shows — but the roadmap reads *"here is what the next set of expectations looks like"* with **no step number and no "you are here" marker**. Of A2's three options this is (b): hiding the roadmap too would discard the transparency he asked for twice in order to hide a label, and hiding "the number only" while showing *"your next step is 2.4"* discloses the level anyway. **The pay proposal that follows a step change cites the roadmap it fulfils** — his own logic (*"the expectation from the employee is if they satisfy in next level the compensation review based on that"*) made visible instead of implied. **No compensation dependency** — this ships in W1, before any pay data exists. **Readiness gate: the Architect has declined to certify this story, correctly — its principal risk is whether the copy reads as expectations rather than as an assessment, and no test he can specify sees that. KAN-207 is Ready when a human has reviewed the copy against the R-17 boundary, and the SPM owns that review.** | **Must · P1** |

### W2 — pay policy, the compensation record, additional pay, and the reconciled ladder (stage **S3**) — R1, R2

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-199 | As a **customer admin**, I want to say which locations share a pay market, so people are only compared against the market they are paid in. (**R5** group key · D1) | A **pay market** is a company-defined grouping of locations, **defaulting to one per `locations.country`**. It is part of the comparison group key and therefore a **hard** prerequisite of KAN-200, and it is the object the **step pay points in KAN-206 attach to**. Carries the annualisation constants — **`monthly_payments_per_year`** (12–14) and `standard_annual_hours` — **on the pay market, not the company**: Acme's Porto office (Portugal, 14 statutory monthly payments) sits in the same company as Hamburg and Tallinn (12), and a company-level constant understates every Porto salary by ~17%, which is more than three times the 5% threshold the feature is built around. A merged **multi-currency** market is **refused** unless an effective-dated FX rate exists for every currency in it — **no silent 1:1, ever**. Thresholds, the coverage gate and the pay-market definition are gated **`company_settings:w`** (seeded PORTAL_ADMIN-only), never a role check. Every change audited. **⚠ A4–A6:** **registers the fifth feature code `pay_policy`** in all four places — Global HR authors the ladder's economics, local HR acts on one person's pay (A6 §5). **Pay markets, the annualisation constants, the materiality threshold and the coverage gate move from `company_settings:w` to `pay_policy:w`.** **CFL-42-20's ruling is preserved** — it is still not a role check, `pay_policy` is seeded HR_ADMIN + PORTAL_ADMIN and a tenant may widen or narrow it in one click — only the home changes, and UX gets **one gate per screen instead of two**. **`pay_policy:r` is required to read entry values and rate schedules**, because under A6 base pay *is* the step's value, which makes the step↔salary inference **exact in both directions** (**CFL-42-59**). The ladder's structure and expectations stay public on `job_architecture:r`; the ladder's **money** does not. | **Must · P1** |
| ⬜ KAN-206 | As a **customer admin**, I want to say what a step is worth, so pay can be checked against the step somebody is actually on — and computed when they move. (**A1 §3** — this is now the reference value for the whole equity feature) | Per **(job level × pay market)**: a **base pay point** (the rate at entry, step `.0`) and a **step increment** — the company-defined percentage the owner meant by "5%". Increment configured **per level with an optional per-step override**. **Compounding: each step's pay point is the previous step's uplifted by the increment — compound, not linear.** His phrasing describes the gap between *consecutive* steps, and the rationale is an adjustment to *that person's* pay. Across a 5-step level at 5% the two readings differ by ~2.1% of salary — small enough that engineering would guess either way and never notice, large enough to be wrong, so it is ruled rather than inferred. Arithmetic per BR-1.5 (exact decimal, no intermediate rounding, HALF_UP once). **The finding boundary is derived, not configured (Wave-5 §16.2, the nearest-step rule).** A finding is raised when an employee's pay is **nearer to a different step's pay point than to their own** — the midpoint between adjacent pay points, on relative (ratio) distance because the ladder is multiplicative. **There is no `tolerance < increment/2` constraint** and no cross-permission-domain CHECK: UAT proved that rule left a *dead zone* flagging ~20% of a perfectly-fitted workforce, and the BA's proposed fix (`tolerance = increment ÷ 4`) would have **doubled** it to 50% — two correct fixes fighting, which is how you know the mechanism was wrong. A **tolerance** survives, default ±2%, stored with the increment on `compensation:w`, but **only as a non-notifying quality measure** ("close, not on the point") shown on the ladder-fit report and the compensation card — it never raises a finding, so nothing constrains it. A **0% increment is permitted as an explicit choice** and marks the level *not evaluable by Check A′*, with the reason named. **One configuration guard remains:** a **warning when a level's base pay point is below the previous level's top-step pay point** — a promotion that cuts pay — shown where the choice is made. Pay points and the tolerance are gated `compensation:w`; the step *count* and *expectations* beside them are `org_structure:w`. **Should · P3 within this story:** the configurator totals the gap between current pay and fitted step pay points, so HR can see the cost of a ladder before adopting it. **Pay points are effective-dated from the start** (half-open, ADR-020's convention) — retrofitting effective-dating is a rewrite, adding it now is a column, and **A2's annual hike cycle makes it mandatory**: a finding raised in 2026 must still be explicable in 2028 after the ladder has been re-based twice. `step_pay_point()` therefore takes an **as-at date** and every caller passes one. **Hard prerequisite of KAN-200, KAN-192, KAN-209 and KAN-210.** **The ladder-fitted-and-reviewed gate ships CLOSED with this story** and is opened only by KAN-209's review — between pay points existing and steps being fitted every employee still sits at `.0`, and the closed gate is the only thing making that window safe. **⚠⚠ A6 §4 — SUBSTANTIALLY RE-SPECIFIED. The rate is per step-transition, per year, set by Global HR.** *"from 2.0 to 2.1 the hike will be 2% this year while from 2.1 to 2.2 it will be 2.4"* — so **`step_increment_pct` on `job_levels` is the wrong shape and is withdrawn**, and **`job_step_increment_overrides` stops being an exception path and becomes the schedule itself**: one rate per transition, **effective-dated with history**, on ADR-020's half-open convention. The two-tier rate/override lookup collapses into one, so this should be **cheaper** than what it replaces. Year-scoping is not optional — a finding raised in 2027 was computed against 2027's schedule, and if 2028 overwrites it the finding becomes inexplicable. **`step_pay_point()` now resolves two effective-dated things at the as-at date** — the entry value *and* the rate schedule. **Compounding survives and generalises:** `point(n) = entry × Π(1 + r_t)` over the transitions, verified against his own arithmetic (€50,000 → €51,000 → **€52,224**; linear would give €52,200). **The tolerance is withdrawn for the third and final time, and there is now nothing left to constrain** — base is *derived* from the step rather than observed, so the check is an equality and there are no adjacent bands to overlap; **R-16 stays closed and no cross-field constraint exists anywhere in the model**. Per-transition rates make any half-increment rule meaningless anyway (2% below, 2.4% above — "half the increment" is two numbers). What survives is a **materiality threshold, company-configurable, default 1%**, and **it governs notification only: the deviation is always computed, always shown in the register with its magnitude, and always counted in the reconciliation totals, whatever the threshold is set to.** A mis-set threshold can suppress noise; it can never suppress fact. **Gated `pay_policy:w`.** | **Must · P1** |
| ⬜ KAN-210 | As a **customer admin**, I want to move the whole ladder's pay rates when the market moves, so the pay-fairness check does not start flagging everybody the first time we grant a raise. (**A2 §5a** · **CFL-42-54**) | **Re-base**: raise every pay point for a job family or a pay market by X%, effective on a date, with a mandatory reason, in **one audited transaction**. **This is the half of the annual hike cycle that stays in EP42, and it is why EP42 is safe to ship whether or not EP43 follows.** Without it, an ordinary hike makes the equity register unusable in a single cycle — with a 5% increment, **any hike above 2.5% puts every employee nearer the next step's pay point than their own**, so a 4% hike flags the entire workforce as `PAY_ABOVE_STEP` (4.00% from their own point, 0.95% from the next). **This corrects A2's own premise that the drift is "silent": under the nearest-step rule it is loud, and it arrives in cycle one rather than cycle three** — worse in volume, better in that nobody is quietly misled. **Every finding is evaluated against the pay point in effect on its evaluation date, and stores that date**, so a 2026 finding still explains itself in 2028. **A staleness warning** in the register where a level's newest pay point is older than the company's configured cycle period (default 18 months): *"these pay points have not been re-based since March 2026; findings may reflect market drift rather than pay decisions."* The re-base screen previews its effect on existing findings before it commits — a bulk action that moves every pay rate in a ladder needs a confirmation proportionate to its blast radius. **Inside a cycle, re-basing is driven by the cycle** (A3-3): a cycle that moves salaries without moving pay points — or the reverse — must not be reachable, and a cycle cannot close having done one and not the other. The re-base percentage is **employer-set, pre-filled from their own hike percentage, editable** — a pre-fill derived from the company's own number is not a product default (A3-1). **The standalone action stays**, because EP42 must be usable without EP43. **Status: a standing assumption awaiting the owner's confirmation** (A3-3 — he did not understand the question the first time and it has been re-put in plain terms); work proceeds on it, and it is in the assumption register rather than recorded as a closed decision. A company without EP43 can run its first hike manually: re-base here, adjust salaries through KAN-195's import, approve through the existing chain. **⚠ A6 — PROMOTED IN IMPORTANCE, and the re-basing question it existed to answer is DEAD in its old form.** That question assumed an across-the-board hike moving salaries independently of the ladder, and assumed base and the step's value can drift apart. Under A6 neither is true: **base pay *is* the step's value, so moving the ladder and paying people are the same act.** Raise step 2.1 from €51,000 to €52,020 and every employee at 2.1 is, by definition, owed €52,020 — there is no second operation to keep in sync. So this story stops being *"a maintenance action that keeps the check honest"* and becomes **the mechanism by which a company grants an across-the-board rise**, which is why it stays firmly inside EP42. **Also carries the annual re-authoring of the per-transition rate schedule.** **Gated `pay_policy:w`.** **What survives of the old question is one narrower, genuinely new one — *does the entry value of a level move each year?*** — i.e. *what does Anna, who stays at 2.1 all year, earn next year?* Put to him as **Q1** with three options and three numbers (§22.13). Default being built: **employer-authored, effective-dated, no annual expectation imposed** (A3-1), **plus a staleness warning** at 18 months. | **Must · P1** |
| ⬜ KAN-193 | As **HR**, I want the product to hold an effective-dated salary for an employee, so pay is a governed record rather than a spreadsheet. (**R1** — the spine of the epic) | **Append-only, effective-dated** compensation history: amount (`NUMERIC(14,2)`, exact decimal, major unit, **> 0**), ISO-4217 currency (always explicit, never defaulted), **FTE** (0.01–1.00, mandatory and **defaultless for `PART_TIME`**), pay basis (`ANNUAL`/`MONTHLY`/`HOURLY`), `effective_from`, actor, mandatory reason, correlation id. **No UPDATE and no DELETE path** — a correction is a new record, a void is a marked record (`compensation:d`). "Current" is **computed, never stored** — a stored `is_current` on a future-dated row would need a scheduler that does not exist. Half-open intervals with a GiST non-overlap constraint; a same-date correction is permitted and tie-broken by `created_at` with the superseded row marked, so "current salary" always returns exactly one value. Money never crosses the wire as a float. Written inside the caller's `transaction()` with its audit row. `retention_class = 'EMPLOYMENT'`. Non-ACTIVE employees: history readable and retained, new records refused except a correction. **⚠ A6:** the record now carries **base and additional pay as two distinct, separately-governed amounts** (KAN-218). Nothing may sum them into a single "pay" figure in the schema, the API or the UI — that would undo A6 on the screen. §18.1's naming rule extends: **base is named "base" everywhere**, and additional pay sits beside it rather than inside it. | **Must · P1** |
| ⬜ KAN-194 | As an **employee, manager and HR admin**, I want to see exactly the pay I am entitled to see and nothing else, so the most sensitive data in the product is safe by default. (**D5**) | Three feature codes registered in **all four places** — `compensation`, `compensation_self`, `pay_equity`. The default matrix as a ceiling a tenant may widen or narrow **with no extra checks in any route**: manager sees **direct reports only, not the subtree**; department and location heads **nothing** by default; `COMPANY_ADMIN` **nothing** by default; employees see their own via `compensation_self`. **Row scoping lives in the service layer** and is documented as *not* the forbidden sub-flag — the flag says whether you reach the surface, the scope says which rows it returns, which is what company scoping already does everywhere. "**My Pay**" server-scoped to `session.employee_id`, never from a parameter. `r`/`w`/`d` separable; a `w`-less holder gets a refusal with **no state change**. **An amount is absent from the JSON payload, not hidden in the DOM**, for every role lacking scope, across all thirteen enumerated surfaces. The Feature Access tab **states the scope consequence next to the grant**, so a grant that yields nothing does not read as a bug. **The employee STEP-disclosure switch lives here** (A2 §6, corrected by A3-4 / **CFL-42-58**): the switch governs the **step**, because the job title already discloses the level. When off, the employee still sees **their role, their job family and every level's expectations** — the ladder is public — but **no step number and no "you are here" marker anywhere in their own view**, and **My Pay drops every pay-point reference, not merely the step number**: a level's base pay point plus a published increment plus your own salary lets you compute your step, which is CFL-42-39's inference class again. OQ-BA-12's default becomes conditional. **Per company, not per employee.** **The switch governs the employee's view of their own level and nothing else** — never the manager (they author the roadmap and cannot do it blind), never HR, never the register, never reporting, never the audit trail. A switch that over-applies is as much a defect as one that leaks, and both directions are asserted. **CFL-42-57:** an employee who is *also* a manager will see their reports' steps and not their own — the correct output of two orthogonal rules, and UX owns copy that stops it reading as a bug. **Cross-tenant subject ids return `404`, not `403`** — a 403 confirms the id exists, which is an existence oracle over the most sensitive population. **Ships in the same release as KAN-193.** **⚠ A6:** the visibility model covers **additional pay** exactly as it covers base — `compensation:r`, absent from the payload for anyone without scope, in **My Pay** for the subject. **The step-disclosure switch is CLOSED** (A5 §1). **CFL-42-59:** base *is* the step's value under A6, so step and salary are now **exactly** invertible in both directions — where step display is off, entry values and rate schedules must also be unreadable by that employee (`pay_policy:r` is not granted to `EMPLOYEE`), and My Pay's existing rule extends to the `/ladder` surface. | **Must · P1** |
| ⬜ KAN-218 | As **local HR**, I want to record money an employee receives **outside** the ladder, with a reason, so a retention save does not corrupt the ladder. (**A6 §3** — the owner's own mechanism) | **Base pay and additional pay are two distinct, separately-governed amounts.** Base is governed by the step and moves only when the step moves or the ladder moves; **additional pay is a human decision for a named reason, outside the ladder.** His example: Tom is at 2.1 on €51,000 and about to resign; local HR grants 5%. **Tom stays at step 2.1, base stays €51,000, and €2,550 is recorded as additional pay with a reason.** Total cash €53,550, and the correspondence check raises **nothing** — *"that does not mean he will be assigned to 2.4 or 2.3 just to match the salary."* **Mandatory reason code** from a seeded, company-editable list (`Retention` · `Market premium` · `Red-circled legacy pay` · `Temporary responsibility` · `Location or assignment allowance` · `Transitional (ladder adoption)` · `Other (text required)`) — free text alone is unreportable, and legibility is the entire value of the field. **Effective-dated from the start** (half-open, ADR-020). **An optional end date; where there is none, a mandatory review date, default 12 months** — a premium nobody revisits becomes invisible permanent salary, but a hard expiry would silently cut somebody's pay on a date nobody remembers, so it **never auto-expires and always comes back and asks**; premiums past their review date surface in the register with their age. **Granting it is a `COMPENSATION_REVIEW` on the existing engine and KAN-198's four-eyes applies** — two different people, initiator may not approve; discretionary off-ladder money is not *less* consequential than base. **Excluded from the step-correspondence check** (base only — the whole point is that it sits outside the ladder) and **included in Check B** (a gap paid through premiums is still a gap). An amount in every respect: `compensation:r` to see it, **never in an `audit_log` diff** (ADR-019's per-action allowlist extends to it — `has_additional`, `reason_code`, `direction`, `pct_change_band`, effective date, **never a figure**), absent from every payload without scope, in the watermarked export, and in **My Pay** for the subject. **An additional-pay register** with, **Should · P3**, the **per-level share report**: a level where a third of total cash sits outside the ladder is a level whose ladder is set wrong, and that is more actionable than any individual finding (**R-21**). **Not a components model** — one named component is not `compensation_components`; §18.1's extensibility rule already records that shape, and OQ-5 stands at base only. | **Must · P1** |
| ⬜ KAN-195 | As **HR**, I want to load our existing salaries in bulk and fix individual rows by hand, so we can get to usable coverage in days rather than a quarter. (**R2** · D7) | CSV import with **dry-run → diff → commit**, reusing the EP35-S2 surface, never a second importer; the amount column is named **`amount`** (not `annual_base`, which would hold a monthly figure and produce a first import wrong by a factor of twelve); row-level errors reported with reasons — **it must not inherit DEF-42-1's silent-`SKIPPED` pattern**; a file that would write null or zero over an existing salary is rejected at preview; atomic per batch. Single-employee manual entry gated `compensation:w`, with a **mandatory reason category** from a seeded, company-editable list (`Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other`) plus optional free text. **"No salary recorded"** and **"Not applicable — contractor rate recorded"** are two distinct empty states that must never look like a value or like each other; a contractor's rate **may** be recorded (blocking it pushes it into a spreadsheet, which is the problem we started with) and is excluded from comparison with the exclusion counted. **Pay coverage** and **level coverage** are reported as two separately named figures, each naming its denominator. **No derived, estimated or imputed salary anywhere, ever.** **⚠ A6:** the import and manual entry carry **additional pay** alongside base, with its reason code and dates. **The importer may never infer, suggest or default a step from an imported salary** — that is the A6 prohibition, and it must be asserted by a negative test rather than assumed. | **Must · P1** |
| ⬜ KAN-209 | As **HR**, I want to reconcile what people are actually paid against what their step is worth, decide each difference once, and only then let the fairness check run. (**A6 §2** — replaces the forbidden step-fitting backfill · **the W2 exit gate**) | **⛔ The previous content of this story — *"fits the step to the pay, not the pay to the step"* — is FORBIDDEN by A6 and is withdrawn in full.** Fitting a step from a salary is the model the owner rejected. The step now comes from the **job**, assessed by the employee's manager in **KAN-191 (W1)**. This story handles the other half — and it has to solve the day-one alert storm that fitting used to hide. **For every assessed employee, compare recorded base with the step's value as at the reconciliation date, and require one recorded disposition each before Check A″ may run for that company.** **It opens with the totals, not a list**, because the HR director's first question is *"what does adopting this ladder cost me?"* — *"132 of 146 assessed · 89 already match · 31 below their step value by €214,000 · 12 above by €58,000 · 14 not yet assessed."* **Three dispositions, mandatory, none pre-selected: (1) Align** — set base to the step's value on an effective date, reason `Ladder adoption`; **(2) Attribute the surplus as additional pay** (KAN-218) with a reason code and a review date — available only where base > step value, and it is exactly what A6 §3 invented the field for, applied to history; **(3) Accept a residual deviation** with a mandatory reason and a review date, producing a finding that is **already dispositioned `JUSTIFIED`** the day the gate opens. **Approved once, as a batch, by two people** — routing 31 individual requests through the chain would guarantee the work never finishes; **KAN-198's four-eyes binds the batch** and the person who prepared it may not approve it. *(This sets the precedent EP43's cycle approval inherits — better established here on 146 rows than invented later on 500.)* **Opens the ladder-adopted-and-reconciled gate** (renamed from ladder-fitted-and-reviewed), which **ships CLOSED with KAN-206**. **Unassessed employees do not block the gate** — they block only their own evaluability, and they are counted and shown. **Day-one finding count is zero by construction** — the same outcome the withdrawn nearest-step rule achieved, reached **honestly**, because a human decided every case rather than because the system quietly re-labelled everyone's step to match their salary. **Also reports ladder-description completeness** ("28 of 34 steps described") — A2 §4 makes completeness a launch expectation, and under A6 an undescribed ladder cannot be assessed against at all, so **R-18 is now a hard adoption dependency** rather than a quality worry. | **Must · P1** |

### W3 — coupling to the workflows (stage **S3**) — R3, R4

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-196 | As a **manager or HR admin**, I want a position change to carry its pay decision through the same approval, so a move is never applied with the pay question unanswered. (**R3** · D4) | The compensation block lives **inside** the shared `_move_modal.html`. The pay decision is **mandatory to answer, not mandatory to change** — *No change · New salary · Defer (reason required)*, **nothing pre-selected**. A money-bearing request is **refused at create time** if any chain step has no approver holding `compensation:r` (using KAN-188's non-session resolver), naming the step and writing nothing. **A manager without `compensation:r` cannot route around the control**: their request records `NOT_ANSWERED_NO_PERMISSION` and **the first `compensation:r` approver must answer before approving** — the question is always answered before apply, and the manager still sees no pay. **The apply never writes null or zero over an existing salary** (the D-185-1 pattern in a worse form), with a named regression test across five proposal shapes. The block is **absent, not disabled**, for a user without `compensation:r`. Placement and pay share the KAN-189 effective date. Money lives in a **one-to-one child table** so existing queries cannot return it. **⚠ A4–A6:** the compensation block carries **additional pay** as well as base, and gains the same **inline deviation warning at proposal time** as KAN-192 — advisory, overridable with a reason category, visible to the chain. **The Category 2 integrity controls in this flow are not affected by advise-don't-block and may not be weakened by citing it** (§22.7.1). | **Must · P1** |
| ⬜ KAN-197 | As **HR**, I want a level change to be a first-class request with a salary review that cannot be skipped, so a promotion never quietly happens without a pay decision. (**R4** · closes backlog open items #3 and #4) | `request_type` ∈ `TRANSFER` · **`LEVEL_CHANGE`** · `COMPENSATION_REVIEW`, every existing row defaulting to `TRANSFER`. **Named `LEVEL_CHANGE`, not `PROMOTION`**, with a stored `direction` of `UP`/`DOWN`/`LATERAL` — D3 permits downward and sideways moves, and a display label cannot fix an audit trail that says `PROMOTION_APPLIED` for a demotion. **"Promotion" remains the word shown to users when the direction is UP**, which is what R4 asked for. All three types run on the **existing** engine and chain — no second engine. A `LEVEL_CHANGE` proposes a new (family, level, step) and may also change placement; **"no change" on an upward move requires an explicit recorded reason**. A company may configure a **different chain per type**, falling back to the `TRANSFER` chain so no request ever runs with no chain. Type is inferred from what changed in the shared modal. Applied atomically with the level assignment and the compensation record — **one transaction or it is a bug**. | **Must · P1** |
| ⬜ KAN-198 | As a **compliance owner**, I want two different people required on any approval that moves money, so a two-level control is not one person twice. (D4h · **backlog open item #5**) | For any request carrying a **compensation or level** change: a user who has decided one level **cannot** decide another on the same request; **the initiator may not decide any level** (without this, an HR_ADMIN who also holds PORTAL_ADMIN raises a pay rise and satisfies level 1 by role — the control passing while doing nothing); **not configurable, not overridable, and not bypassable by SYSTEM_ADMIN** — a control with a hole exactly where the demo identity sits is not a control. A money-bearing request **requires ≥2 independently satisfiable levels and is refused at create time** otherwise — **and this is not an enhancement, it is the difference between KAN-198 existing and KAN-198 working.** Evidence (Architect V18): `_DEFAULT_STEPS` is a **single** `HR_ADMIN` step and `select count(*) from org_change_workflows` returns **0** — **no tenant has configured a workflow at all**, so four-eyes as originally designed would have shipped, passed every test, and **bound nobody in any tenant**. A **seeded two-level default chain** (HR_ADMIN → PORTAL_ADMIN) therefore ships for the money- and level-bearing types, and the create-time refusal also covers the case where one person is the only possible approver at two levels (**CFL-42-26**). **The administrative remedy for a stuck chain is `cancel` (which applies nothing) plus reconfiguration — never `approve`**; if no cancel path exists it is added here. The approval-chain admin page **shows the overlap at configuration time**. Placement-only requests: warn, allow, record as a self-approval. Behaviour changes for EP27 and EP38 too; both regression suites extended. | **Must · P1** |
| ⬜ KAN-192 | As a **manager or HR admin**, I want step advancement to be an explicit recorded decision taken at a review, which **proposes** the matching pay adjustment rather than applying it. (**R6** · **D3.4** · **A1** — **OQ-1 CLOSED: confirmed not automatic**) | Step advancement is an explicit audited action carrying a **mandatory `review_context`** — `PROBATION_REVIEW` · `MID_TERM_GOAL_REVIEW` · `PERFORMANCE_REVIEW` · `OFF_CYCLE` — plus a review date and optional note. **Mandatory to answer, with an off-cycle option**, mirroring D4c: an unanswered context means the question fell on the floor. **EP42 records that a step change happened at a review; it does not build the review** — no cycles, no scheduling, no reminders, no goals, no ratings, no calibration, no probation entity. **Advancing a step pre-fills a `COMPENSATION_REVIEW` at the new step's pay point and routes it through the existing chain — it never applies a pay change.** Four reasons converge: A1 makes progression a human mutually-agreed decision, an auto-applied change has *zero* eyes against KAN-198's four, it would hand every manager a unilateral pay lever against D5, and `CLAUDE.md` invariant 3 forbids applying before final approval. The pay answer is **mandatory and may be "no change" with a reason**. **The step may land before the pay does, and that is deliberate** — it produces exactly the `PAY_BELOW_STEP` condition Check A′ exists to detect ("they took the responsibility, the pay never followed"), so the two halves of A1 fit together without forcing them into one transaction. The step change itself does **not** go through the approval chain — it is within-position job content; a **level** change does, via KAN-197. No bypass: the step has no chain, the money always does. **No automatic roll-up** on reaching the top step — a signal to **the reporting manager only** (A1 narrows this from Wave 1's manager + `compensation:w` holders; HR sees it in the register, not as a notification), worded with **no implied promise**, and the subject is not notified. **Step position is a live report of scope taken on** — the register and team view show step distribution, so a manager can see who has quietly taken on more, which is where the "pay never followed" cases are actually spotted. **A single action advances at most ONE step.** A move of more than one step is **refused, directing the user to raise a `LEVEL_CHANGE` request** — which has a chain and two pairs of eyes. This closes a control gap A1 created (**CFL-42-49**): a step change is applied by one person with no approval and now has a computable pay consequence, so a manager could move a report 1.0 → 1.5 alone, lift the expected pay point ~27%, and manufacture a `PAY_BELOW_STEP` that pressures the organisation to pay it. One step is the principled bound rather than an arbitrary cap — under A1 a step is a *described set of expectations an employee has demonstrably met*, and meeting two steps' worth at one review is a correction or a promotion, not progression. The capability §14.3.4 permits is preserved, just routed through governance. Downward moves permitted with a mandatory reason; the register's *"on step X since"* line makes the pattern visible to HR, which is the real defence. **The audit row records step before → after and never the pay point** — that is an amount, and amounts stay out of `audit_log`; the pay consequence is derived on read by a `compensation:r` holder. Depends on **KAN-206**. **⚠ A4–A6:** the pre-filled proposal now comes from **that transition's** rate, not from a level-wide increment. **+ the inline deviation warning at proposal time** (A4 §2 — *"the application will raise red flag if the hike is made beyond the set levels to manages"*): where the proposed amount is edited away from the transition rate, the deviation is shown inline with its magnitude and submitting requires a **reason category**. **It is advisory and overridable — a judgement about an amount is Category 1** (§22.7.1) — with a recorded actor, a mandatory reason code, an audit row carrying **no figure**, and **visibility to the approval chain at decision time, not merely a log entry**. The one-step-per-action rule and everything else in this story stand. | **Must · P1** |

### W4 — pay equity (stage **S3**) — R5

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-200 | As **HR**, I want the system to tell me where somebody's pay does not match the step they are on, so I find it before they or a regulator does. (**R5** · **D1 re-ruled by A1**) | **Check A′ — step-pay correspondence. Absolute, not statistical.** The reference is **the employee's own step's configured pay point** (KAN-206), not a group median and not a band midpoint. **No minimum group size — n = 1 is a valid, meaningful check. No coverage gate.** Two finding types with **asymmetric severity**, because the owner's stated concern is directional: **`PAY_BELOW_STEP` is primary** ("they took the responsibility, the pay never followed") and **`PAY_ABOVE_STEP` is secondary**, lower severity, different copy — it is legitimate far more often than not (market premium, red-circled legacy pay), and weighting them equally fills the queue with things nobody should act on. **Flag when the employee's pay is nearer to a *different* step's pay point than to their own** — they are recorded at 2.4 and paid like 2.2 (Wave-5 §16.2, the nearest-step rule). The boundary is **derived from the increment, not configured**, which makes the dead zone **zero by construction** and means a correctly fitted backfill raises **no findings on day one** — the previous tolerance-based rule flagged ~20% of a perfectly-fitted workforce, which UAT quantified as 4 findings from 10 employees who had all been fitted correctly. It still catches everything the feature exists for: one unfollowed step advance moves the expected point a full increment (−4.76% at 5%), comfortably past the half-increment boundary. Trade-off, stated: **Tier-1 sensitivity is no longer tunable** — a company wanting finer detection shortens its increment, i.e. says something true about its ladder, rather than turning a detection dial. Deviations *within* the nearest-step band but outside the display tolerance are a **non-notifying quality measure**, never a finding. **Per-employee evaluability preconditions**, each counted and named, never silent: a current level **and step**, a current compensation record, a resolvable pay market, a configured pay point, ACTIVE, not CONTRACTOR or INTERN. **Check A′ does not run for a company until its level/step backfill is marked reviewed** (KAN-191) — this replaces the withdrawn 80% coverage gate. **R5's original ask is still satisfied by construction:** two people at the same step are measured against the same pay point, so a gap between them still surfaces. **Check B — group gender pay gap — survives statistically intact and unchanged:** group `(company, job_family, job_level, pay_market)`, **n ≥ 5**, ≥ 2 of each gender compared, median arithmetic including the even-group case, `OTHER`/`NULL` excluded-counted-and-shown, flag on **`|gap|` ≥ threshold** with direction recorded. Step is added to Check B as a **reported dimension** — a gap is more informative when you can see whether the women in a level sit at lower steps — **but the step-distribution report is rendered only at n ≥ 5 and only to holders of both codes where any value is invertible** (**CFL-42-38**: the distribution the SPM asked for in §14.3.4 is an aggregate, and his own CFL-42-32 forbids aggregates below five). **Another employee's step position is scoped exactly as their pay is** (**CFL-42-39**): base pay point + published increment + known step = that person's salary, so `job_architecture:r` seeded to everyone is right for *expectations* and wrong for *other people's steps*. Own step always visible; level titles and generic expectations stay public. **CFL-42-32 stands: no aggregate of any kind rendered below n = 5**, minimums floored in the database. Compared value = **FTE-normalised annualised base**; `HOURLY` records are **not** FTE-divided twice (the most likely arithmetic defect in the epic). **The comparison uses the same rounded value the UI displays**, so a finding is always reproducible from the screen. Thresholds and tolerance per company, gated `company_settings:w`. **Event-driven after commit plus an on-demand run — no batch.** Every screen states this is a **measurement, not a compliance conclusion**. **⚠⚠ A6 — CHECK A″ IS AN EQUALITY, NOT A SEARCH.** The nearest-step rule is **withdrawn in full, as a mechanism and as a description.** Compare **`base` with `step value(as_at) × FTE`** and state the difference as a **magnitude in currency and percent against their own step** — *"base is €2,430 (4.8%) below the value of step 2.4"*. **No copy, tooltip, export, notification, API field or audit row may reference any step other than the employee's own**: *"paid closer to step 2.2"* is a claim about somebody's step, and standing rule 6 forbids a label that claims more than it should. **This is a prohibition and it needs a negative test, not a comment.** Withdrawn with it: the tie rule, the relative-vs-absolute distance metric, the half-increment boundary and every fixture that computes a nearest step — **deletions, not rework**, and the computation gets markedly cheaper. **`PAY_BELOW_STEP` stays primary and `PAY_ABOVE_STEP` stays secondary and silent**, but `PAY_ABOVE_STEP` **changes meaning**: it no longer hints that somebody is "really at a higher step" — under A6 over-payment has a legitimate home, so a residual means **"this base was set off-ladder and nobody attributed the difference"**, which is a governance signal and should be rare. Evaluability preconditions gain **`STEP_NOT_ASSESSED`**. The gate this check waits on is renamed **ladder-adopted-and-reconciled** and is released by KAN-209. **Check B is unchanged in content and ⬜ conditional in status** — see the conditional slice below. | **Must · P1** |
| ⬜ KAN-201 | As the **pay-equity responsible**, I want each finding to reach me, stay in one place until I have dealt with it, and then go away, so the queue is worth working. (**R5** delivery · **D2** · **A1**) | **Three finding types with distinct copy, severity and disposition categories** — `PAY_BELOW_STEP` (primary) · `PAY_ABOVE_STEP` (**secondary and SILENT — register only, no bell entry, no badge**) · `GENDER_GAP`. Silent is a legitimate expression of "lower severity" when the alternative feeds R-1: a notification whose honest review outcome is *"nothing to do"* is how a channel gets muted, and this channel is shared with the primary check; raising one pay point creates dozens of `PAY_ABOVE_STEP` at once (**CFL-42-48**). **`reference_value` and `deviation_pct` render only to holders of both `pay_equity:r` and `compensation:r`** — `reference_value × (1 + deviation/100)` is the subject's salary, so a stored column inherits CFL-42-19 exactly as a computed ratio does; `GENDER_GAP` findings carry no `reference_value` at all, enforced by CHECK (**CFL-42-44**). **A `PAY_BELOW_STEP` finding carries its own remedy: a "Propose adjustment" action** that pre-fills a `COMPENSATION_REVIEW` at the step's pay point and routes it through the existing chain, retiring the finding as `RESOLVED` when the pay lands. The finding and its fix in one place — this is the most useful thing A1 makes possible and it existed in no Wave 2 document. Recipients = holders of `pay_equity` read in that company **plus** an optional per-company named escalation list that **adds recipients and can never remove access**. Primary surface is a **register** at `/compensation/equity`. **Bell: a new "Pay Equity" section**, feature-gated, hidden when empty, icon **⚖️** in `NOTIF_ICON` (never ❌), **one quick action "Review →"** deep-linking to the filtered register — no dispose-from-the-bell, because a disposition without a recorded reason is not auditable. **The badge counts findings with no owner, not all open findings** — dispositions legitimately take days against a 15-working-day median target, and a permanently non-zero badge destroys the signal for the approvals sharing it; `[ Take ]` is a recorded, audited act that decrements it while the finding stays open. **Notification bodies contain no amount and no invertible percentage.** A numeric measured value renders only to holders of **both** `pay_equity:r` and `compensation:r` — a compa-ratio against a known band is a salary. Lifecycle `OPEN → JUSTIFIED / REMEDIATION_PLANNED / RESOLVED / RESOLVED_BY_DATA`, **mandatory reason on every disposition**, category on `JUSTIFIED`. **Retires via `resolve_related()` on disposition for every eligible recipient — not on read.** A `JUSTIFIED` finding does not re-fire within its validity window (default 12 months, inclusive of the last day) unless the gap widens **strictly beyond** threshold + 2pp, the subject's level/step/salary changes, or the configuration changes. **The subject of a finding may read it but has no disposition controls.** No bulk disposition. **⚠ A6:** three finding types remain, and **`PAY_ABOVE_STEP` gains the quick action "Attribute as additional pay"** beside `PAY_BELOW_STEP`'s "Propose adjustment" — under A6 the over-payment case has a legitimate home (KAN-218) and a finding should carry the route to its remedy. **All copy must state the deviation against the employee's own step and never name another step.** `GENDER_GAP` is ⬜ **conditional**. | **Must · P1** |
| ⬜ KAN-202 | As **HR or a compliance owner**, I want to see how someone's pay and their step got to where they are, without pay amounts leaking into the audit trail. (D5.6 · **A1**) | A per-employee **compensation timeline** (effective date, amount, currency, FTE, level/step, actor, reason), **shown alongside the step and roadmap timeline** — "how did this person get here" is one story, not two, and after A1 the step history is what explains the pay history. Gated `compensation:r` and row-scoped, joined to `audit_log` by **`correlation_id`** so the two read as one story. `audit_log` diffs carry **no amounts** — `has_change`, `direction`, `pct_change_band` (half-open buckets on the absolute percentage), `currency`, `effective_date`, level/step before→after only — enforced by a **per-action closed diff-key allowlist**, which is stronger than guessing key names. **The guarantee is scoped honestly: it covers structured fields only.** `reason` is mandatory human free text and no key-matching guard can see into it, so it is a **category + optional text** with a non-blocking numeric-pattern warning at entry, and the acceptance criteria must **not** claim a guarantee the mechanism cannot give. Holding `audit_log:r` alone never reveals an amount. Also delivers a **deliberately designed, row-scoped, audited, watermarked salary export** (`COMPENSATION_EXPORTED` with row count and scope) — HR will ask within a week of go-live, and designing it is much better than someone adding an unaudited CSV button. **⚠ A4 §2:** **+ override-rate and additional-pay-share reporting, Should · P3.** *"A company whose managers override 80% of flags has a mis-set band, and the product should be able to show them that"* — his line, and the most useful sentence in A4. Override rate per company, per level, per market, per reason code, with a **configuration-review tripwire at 40%** matching §1.5's existing "> 40% dispositioned JUSTIFIED" rule — one number, one meaning, two instruments. Above it the register says so in words: *"managers have overridden 62% of pay flags at level 2 in the Nordics. This usually means the ladder's rates are set below the market, not that 62% of decisions were exceptional."* Paired with KAN-218's per-level additional-pay share — **a high override rate and a high premium share are the same disease seen from two angles, and both say the ladder is wrong.** **+ the timeline shows base and additional pay as two series, never summed into one line.** | **Should · P2** |

**Removed from EP42 by A6 — recorded, not lost:**

| Story | Where it went | Why |
|---|---|---|
| **KAN-205** — salary bands as the level's min/max envelope | **Later** (roadmap §E) | Under A6 an employee's base pay **is** the step's defined value, so "is this pay sane for this level at all?" is answered **exactly** by the step value where a band answered it approximately. Keeping it would be carrying a second, weaker reference value alongside the real one. **Deleting a story is the right direction after an amendment that simplifies the model** (SPM challenge pass, §22.1.3(c)) |

### Conditional slice — the gender pay-gap check (**Check B**) — ⬜ **not scheduled; awaiting the owner's answer**

> **⚠ Check B was never the owner's requirement.** It originated in the SPM's own reading of the EU Pay
> Transparency Directive (baseline **S13**, labelled *Assumption / Medium confidence, not verified against any
> source in this repo*) and then travelled through five rounds of documents looking like his. **OQ-3 was
> recorded "closed by reinterpretation" in A1 — but the reinterpretation settled what "5%" means, and never
> asked whether he wants a gender check at all.** Found by the SPM's challenge pass
> (`EP42_SPM_SCOPE_AND_DECISIONS.md` §22.1.3(a), **CFL-42-61**).
>
> **Ruling: kept, re-labelled a *team* requirement, and descoped from the critical path into this separable
> slice.** Nothing else in EP42 depends on it. **KAN-208 comes out of W0 with it**, which also takes **R-19**
> (the vacation-eligibility side effect of populating `employees.gender`) off the critical path entirely.
> Check B's content in KAN-200/201 and every one of UAT's statistical fixtures are **preserved and paused,
> not deleted** — if he says yes, we want them intact.
>
> **His original ask is satisfied without it.** Under A6, two people at the same step in the same market earn
> the same base **by construction**, so a "5% difference for the same position" cannot arise quietly at all.
>
> **Put to him as Q4 in §22.13** — build it / drop it / park it. **SPM recommends park.**

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-208 | As **UAT and anyone demoing this**, I want the seeded population to carry gender values, so the gender pay-gap check has data to run on. (**A1 §4** — owner-authorised) | `employees.gender` is NULL for 100% of the seeded population (DEF-42-3), so Check B would report "insufficient gender representation" for every group in every tenant and could not be demoed at all. Assign values across the seeded population **in the seed files *and* a migration** — a dev DB updated by hand while `seed_data.sql` / `telia_seed.sql` stay unchanged is exactly the DEF-004 trap that broke CI on 9 Aug. **Deterministic and reproducible**, not per-row random, and **shaped so at least two comparison groups satisfy Check B's minimums** (n ≥ 5 with ≥ 2 of each gender) — an assignment that leaves the check undemonstrable has not done its job. `OTHER` is present in the population, because the excluded-and-counted path needs a fixture. **⚠ This changes live behaviour in a shipped feature, and neither the owner's answer nor the SPM's §14.6 spotted it (CFL-42-43).** `employees.gender` has exactly **one** consumer today — vacation-type eligibility (`app/helpers.py:223, 269-280`) — so going 100% NULL → 100% populated **changes which leave types 146 employees are offered.** That is a behavioural change, not a test-data tweak, and the BA logged their own earlier assumption as **KNOWN TO BE FALSE**. **SPM ruling: acceptable on synthetic data, conditional on evidence** — (a) run the vacation regression suite before and after and **explain every single difference**, because a difference nobody can explain is a defect and not a side effect; (b) review every gender-restricted seeded vacation type against the new distribution; (c) the release notes and any demo script state it; (d) **if the diff produces a failure that cannot be explained as intended eligibility change, KAN-208 does not land.** *Partial population was considered and rejected:* it would preserve current behaviour but muddle Check B's exclusion counts and leave "insufficient gender representation" in exactly the groups you would want to demo. **The distribution assertion moves to a W2 exit gate** (**CFL-42-42**) — a comparison group needs a family, a level *and a pay market*, and pay markets arrive with KAN-199 in W2, so it cannot be verified in W0. **Synthetic only:** this does not authorise collecting gender from real people, does not affect T5, and **does not close DPO-1** — having the data does not make processing it lawful, and gender is a special category under GDPR Art. 9 on most readings. | **Conditional · P3** — nothing depends on it |
| ⬜ *(within KAN-200)* | **Check B — the group gender pay gap.** | Unchanged in content from the W4 row above; **changed in status to conditional.** Group `(company, job_family, job_level, pay_market)`, **n ≥ 5** with ≥ 2 of each gender compared, median arithmetic including the even-group case, `OTHER`/`NULL` excluded-counted-and-shown, flag on `\|gap\|` ≥ threshold with the direction recorded, no aggregate rendered below n = 5. **A6 addition: Check B compares base + additional pay**, because a gap paid through premiums is still a gap and a base-only check would be trivially avoidable. **Blocked on DPO-1** (purpose limitation — `employees.gender` was collected for vacation eligibility) **and on the owner's answer to Q4.** | **Conditional · P3** |

---

**Defects — recorded here, routed to their real owners:**

| # | Defect | Severity | Evidence | Owner / route |
|---|---|---|---|---|
| **DEF-42-4** ✅ | **✅ FIXED in KAN-203 (10 Aug 2026).** **`_can_initiate_for` never compares the initiator to the subject.** It returns `True` for any holder of HR_ADMIN / PORTAL_ADMIN / SYSTEM_ADMIN regardless of who the subject is, **including themselves**. `CLAUDE.md`'s headline org-change invariant says *"An individual employee can NEVER initiate their own move"*; the rule as implemented beneath it grants admins a blanket exemption. **The code matches the detailed rule and violates the headline.** The exemption exists so HR can move *other people*; it was never meant to cover acting on oneself. **The headline is right and the code is wrong.** | **Critical** | `app/routes/org_change.py:55-64`; the only self-check in the product is a display helper at `app/routes/employees.py:126-131`, which says so itself | Pre-existing, raised against **EP27**. **Fixed in KAN-203**, in W0, not deferred to W3 — the exposure is live today and the guard has no EP42 dependency. `CLAUDE.md` reworded in the same commit (Architect owns the file). |
| **DEF-42-5** ✅ | **✅ Subject≠decider FIXED in KAN-203 (10 Aug 2026); initiator≠approver still open in KAN-198.** **`decide()` never compares the decider to the subject or the requester.** It checks the decider against the step and the company, and nothing else. **Combined with DEF-42-4, one HR_ADMIN can raise a position change for themselves and approve it end to end on the seeded default chain, today.** After KAN-196 that becomes a self-approved pay rise. | **Critical** | `app/services/org_change_service.py:222-249`; the seeded Acme chain, where `ingrid.makinen` holds both PORTAL_ADMIN and HR_ADMIN | Pre-existing, raised against **EP27**. Subject≠decider **fixed in KAN-203** (universal). Initiator≠approver is **CLOSED AS ACCEPTED for placement moves by owner Decision D-007 (10 Aug 2026)** — the chain above an IC is not deep enough here for a second approver to be a real control. It is documented, accepted behaviour, not an open defect, and must be disclosed at the top of any gate walkthrough touching the chain. **KAN-198 remains in W3, money-scoped**: D-007 was answered about a desk move, and the pay case has not been put to the owner. |
| **DEF-004a** | **One employee has TWO current `DOTTED_LINE` managers, and the product can only ever show one of them.** Found by the `daterange(from, to, '[)') &&` non-overlap check run against real Postgres while verifying KAN-189 — the only overlapping pair in the whole database, both rows `is_current = TRUE` and open-ended from the same day. `_EMP_SELECT` reads the dotted line with a `LATERAL … LIMIT 1`, so **the second relationship is invisible everywhere in the UI**: it is real data that no screen can show and no user can discover or remove. **Not caused by, and not fixable in, KAN-189** — the org-change engine only ever re-points `SOLID_LINE`, and both rows predate it. The underlying cause is **TD-22**: `manager_relationships` has no uniqueness or non-overlap constraint, so nothing stops a second current row being written. **Whether an employee may have more than one dotted-line manager is a product question, not an engineering one** — a matrixed organisation legitimately might, in which case the defect is the `LIMIT 1`, not the data. That decision is needed before either is touched. | **Medium** (1 employee today; the constraint gap is unbounded) | `psql`: `employee_id e0000001-…-042`, 2 current `DOTTED_LINE` rows both from 2026-04-25; `app/helpers.py` `_EMP_SELECT` dotted-line `LATERAL … LIMIT 1` | **Raised 10 Aug 2026 during KAN-189 verification. Deliberately NOT fixed there** — silently deleting one row would destroy information, and silently showing both would change a product behaviour nobody has asked to change. **Needs the owner's call on multiple dotted lines**, then either the `EXCLUDE` constraint from TD-22 (which ADR-020's convention makes a drop-in) or a UI that shows all of them. |
| **DEF-42-1** | **The CSV employee importer cannot write a valid `employment_type`, and fails silently when it tries.** `EMPLOYMENT_TYPES` contains `FULL_TIME` (which the DB CHECK rejects) and omits `PERMANENT` (which it requires); a blank cell defaults to `FULL_TIME`; the resulting CHECK violation is caught and the row is marked `SKIPPED` **with no reason surfaced to the user** — the DEF-002 shape. | **High** | `app/services/import_service.py:16, 63-67, 152, 161-165` vs `database/schema.sql:421-422` | Pre-existing, raised against **EP21**. **Not absorbed into EP42** — EP42 did not break it, and burying it would misattribute the cause. **P1, scheduled in S2, before KAN-195 starts.** EP42 keys its exclusions and FTE handling on `employment_type` and bulk import is the only bulk path. |
| **DEF-42-2** | **`manager_relationships` rows are closed without an `effective_to`** — 2 such rows in the dev database. The pattern EP42 was told to copy for effective dating is undated on its closing side. | **Medium** | `app/services/org_change_service.py:381-385` vs `:370-374` | **Fixed inside KAN-189.** Cheap to fix in the same change; expensive once copied into three new tables. |
| **DEF-42-3** | **`employees.gender` is NULL for 100% of the seeded population**, and there is no admin-facing collection path beyond registration and CSV. | **Medium** (data) | `psql`; `app/routes/employees.py:176-186` | **Product consequence, not a code fix:** Check B has nothing to run on and would report "insufficient gender representation" for every group in every tenant. UAT fixtures must supply it; **Check B must not be demoed on seed data**; and the owner should know, when answering OQ-3, that he may be buying a check that has no data. |

**Open items for the product owner / SPM:**

0c. **Amendments A4, A5 and A6 (2026-08-09) — the owner overturned the pay/step model.** Full re-ruling in
   `EP42_SPM_SCOPE_AND_DECISIONS.md` §22. **The corrected model: job → step → base pay; pay never decides the
   step.** The nearest-step rule is withdrawn in full, step-fitting from salary is forbidden, additional pay
   arrives as KAN-218, the hike rate is per-transition and per-year, `pay_policy` is a fifth feature code, the
   step-disclosure switch is **closed**, and **full performance management is confirmed with the delay
   accepted in the owner's own words** (Decision **D-006**). **Four questions are with him, all with defaults
   being built against and none of them blocking** — the one-pager is **§22.13** and it is written as worked
   examples with his own numbers, per his standing instruction:
   **Q1** does the entry value of a level move each year — *what does Anna, at step 2.1 all year, earn next
   year?* (recommend **C**: employer-authored each year, no automatic rise, with a staleness warning) ·
   **Q2** Global vs local HR — *can Lars in Oslo grant additional pay to a Hamburg employee?* (recommend
   **A**: two permissions, one HR role; organisational scoping is a separate epic) ·
   **Q3** is a discretionary per-employee percentage still wanted (recommend **A**: no — step moves and
   additional pay cover it, **which is why EP43 drops from 7 stories to 5**) ·
   **Q4** did he ever ask for a gender pay-gap check (recommend **park** — see the conditional slice above).

0b. **⚠ Process finding — an unexamined team premise survived five rounds (`CFL-42-60`, §22.15).** *"Pay
   position implies step position"* entered the epic as an SPM inference in §14.1, **was correctly labelled
   an inference at the time**, then acquired a decision number and was cited as a ruling by four specialist
   documents. Its validating question (OQ-A1-1) sat on a one-page list with a default so that *"nothing
   blocks"* — nothing blocked, and nothing was answered. Every tasking brief said **apply**, not **test**.
   And §16.1 recorded *"nobody attacked A1's shape… which is the strongest evidence available that the model
   is right"* — **which is the defect in one line: four specialists tasked from one brief agreeing is one
   assumption wearing four coats, not four pieces of evidence.** The owner was the test, and that is the
   wrong person to be the test. **Three changes, effective immediately for every epic:** (1) a **Load-Bearing
   Premise Register**, max ten rows, each tagged **OWNER / EVIDENCE / TEAM**, with the falsifying question
   named for every TEAM row — **and a TEAM premise may not be load-bearing across more than one wave without
   a validating answer**; (2) **origin tagging on every requirement** in every deliverable — a column, costing
   nothing, that would have carried `TEAM inference — SPM §14.1` in all five documents; (3) **"Premises I
   challenged" is a required section in every specialist report**, containing at least one premise checked at
   **source**. Plus one line for the SPM's review checklist: **agreement between specialists tasked from the
   same brief is not evidence.**

0a. **Wave-5 reconciliation (2026-08-09).** Four specialists amended against A1 and collided on IDs again —
   **CFL-42-35/36/37 were each allocated twice, to different conflicts.** The single authoritative register,
   with the ID mapping for anyone holding an older reference, is `EP42_SPM_SCOPE_AND_DECISIONS.md` §16.3
   (CFL-42-35…53). Two rulings changed this backlog: **the nearest-step rule** (§16.2) and **the corrected
   build order** (§16.5, KAN-209). A **consolidated one-page list of everything still needing the product
   owner's answer** is §17 — that is the page to put in front of him, not this section.

0. **Amendment A1 (2026-08-09) closed OQ-1 and OQ-3.** **OQ-1 confirmed** — progression is not automatic —
   with a richer model that added step expectations, the per-employee roadmap and per-level step counts.
   **OQ-3 reinterpreted** — "5%" is the step increment, not an equity threshold — which withdrew the `n ≥ 3`
   minimum and the 80% coverage gate for the primary check. Three questions replace them, **all with defaults
   so nothing waits**: **OQ-A1-1** confirm the reconciliation of the 5% (*"we will tell HR when someone's pay
   doesn't match the step they're on — is that what you meant?"*) · **OQ-A1-2** confirm that advancing a step
   **proposes** a pay change rather than applying one · **OQ-A1-3** confirm the boundary — **EP42 records that
   a step change happened at a review; it does not build the review**. OQ-A1-3 is the one most likely to
   produce a surprise later, because the owner anchored progression to the performance review, the probation
   period and the mid-term goal review, and **none of those entities exists anywhere in the schema**. A
   Performance, Goals & Reviews epic is recorded in the roadmap's Later list — unnumbered and unscoped.
1. **Seven questions still need the product owner's answer** — OQ-2 (three visibility-matrix cells), OQ-4 (the
   example ladder), **OQ-5 (total compensation — now the *only* one whose late answer forces a rewrite, and it
   got slightly worse under A1: the step pay point is a *base* pay point, so a "total comp" answer would change
   what the increment applies to as well as the record's shape)**, OQ-6 (multi-currency — less pressing, since
   an absolute per-market reference never crosses currencies), OQ-7 (default exposure off), OQ-8 (works
   councils), OQ-9 (segregation of duties, extended to cover the initiator and SYSTEM_ADMIN). All carry a
   recommended default the team builds against today, in the SPM's §6 and §14.9.
2. **Seven DPO/legal items** (DPO-1…DPO-7 in the BA's §4.7.9). **DPO-1 blocks Check B only** — it is a
   purpose-limitation question, because `employees.gender` was collected for vacation eligibility. **DPO-2**
   (does pay history survive erasure, or must it be destroyed) blocks the retention class on KAN-193. The rest
   are launch, not build. Nothing in any EP42 document is legal advice.
3. **KAN-168 (real-DB test tier) is the live scheduling problem.** It is ⬜ not started and it hard-blocks
   KAN-200. **SPM ruling: if KAN-168 slips, W4 slips.** EP42 ships through W3 and the equity engine waits. An
   equity engine certified against mocks is not an acceptable alternative — R-12 and TR-18 are the same risk
   named twice by two roles.
4. **Trigger T5 is added to the D-004 amendment** — *any real, non-synthetic compensation value entered for any
   employee, in any tenant, including a single manual entry by the build team* fires the S5 security phase
   immediately, at a deliberately lower bar than T2. T2 needs a data load; T5 needs one row.
5. **The compensation visibility model is a correctness control, not a security control, until KAN-148 lands.**
   Under demo auth, identity is self-asserted. **Any compensation demo states this at the start**, in the written
   script — not in the answer to a stakeholder's question. A compensation demo without that line is **NO-GO**.
6. **The access model cannot express "read company-wide, write nothing"** — a read-only auditor or works-council
   representative has no clean grant. **Accepted as a named product limitation for this cycle**; no fourth
   feature code and no `scope` column, because changing the platform's access model deserves its own decision
   rather than arriving as a side-effect of EP42. Revisit if OQ-8 comes back "yes".

---

## EP44 — Performance Management  —  ⬜ Planned
**ID:** KAN-219 · **Label:** `performance` `goals` `calibration` `gdpr` `eu-ai-act` `works-council` `stage-S3`
**Source:** the product owner's **Amendment A4** — *"I want a full performance-management capability (cycles,
goals, calibration) a detailed performance requirement impmlemation"* — confirmed with the delay explicitly
accepted in **Amendment A5**: *"OK. go ahead with full implemenation cycle as Product owneer accepting the
delay."*
Business goal **BG7 — Pay decisions this company can defend**. **Sequenced after EP42 and before EP43.**
**Description:** the capability that produces the judgement EP42 and EP43 consume. EP42 records *that* a step
change happened at a review; **EP44 builds the review.** Cycles, goals, self- and manager assessment,
calibration, ratings history, and the two seams by which a rating reaches pay (EP43) and job level (EP42's
step change) — with the compliance gate designed in from the first story rather than bolted on.

> **Decision D-006 — 2026-08-09 — recorded verbatim, because this is exactly the decision somebody
> re-litigates six weeks from now.**
> *Context:* the SPM sized a performance **input** — a manager-entered band per employee per cycle, 2 stories,
> ~2–3 weeks, no delay — against full performance **management** — ~20–25 stories, 12–16 weeks, sequenced
> first, pushing the hike cycle out by roughly a quarter — and **recommended (a) with Confidence High**.
> *Options considered:* **(a)** performance input inside EP43 · **(b)** full performance management as EP44.
> *Decision:* **(b).** His words: *"I want a full performance-management capability (cycles, goals,
> calibration) a detailed performance requirement impmlemation"* and *"go ahead with full implemenation cycle
> as Product owneer accepting the delay."*
> *Rationale:* his, not the SPM's. He named the three things option (b) contained, so this is a considered
> choice against a stated cost, not a misread — and he then accepted the cost **in his capacity as product
> owner and in those words**.
> *Impact:* **22 stories.** BG7 becomes a three-epic programme of ~50 stories and ~8–9 months. EP43 shrinks to
> five. **Recorded as "SPM recommended (a), owner chose (b)". It is not re-litigated here or anywhere.**

> **Decision D-007 — 2026-08-10 — initiator ≠ approver is ACCEPTED AS-IS by the owner.**
> *Context:* KAN-203 closed **subject ≠ initiator** and **subject ≠ decider** (DEF-42-4 / DEF-42-5). The other
> half of DEF-42-5 — **initiator ≠ approver** — was left open by design and scheduled money-scoped in KAN-198.
> Engineering disclosed the live consequence plainly: today an HR_ADMIN can raise a transfer **for somebody
> else** and then approve it themselves, with no second person involved.
> *Decision:* **the owner accepts it and does not want it closed.** His words: *"This is ok because on top of
> Ravi we do not have 2 levels of managers. So that's ok."*
> *Rationale:* his. The chain above an individual contributor is not deep enough in this organisation for a
> second approver to be a meaningful control on a **placement** move; requiring one would add a step that no
> real person is available to take.
> *Status:* the concern was raised once, the owner reaffirmed, engineering proceeded. **Not re-litigated.**
>
> *Two facts recorded alongside it, as facts and not as an argument:*
> 1. **The calculus changes when money enters.** The owner's reason is about org depth on a desk move. KAN-196
>    makes the same chain carry a **pay** decision, where self-approval is a financial control and not an
>    org-shape question. **KAN-198 stays in W3, money-scoped** — this ruling covers placement moves, and the
>    money-bearing case has not been put to him yet. When it is, it should be put as its own question.
> 2. **A deeper tenant changes the premise, not the ruling.** The reason given is specific to this
>    organisation's shape. If a tenant is onboarded with two or more configured approval levels, the premise no
>    longer holds for that tenant and this should come back to the owner — it does not silently expire.
>
> *Not a defect any more.* This is now **documented, accepted product behaviour**, so it must be disclosed at
> the top of any Demo Readiness Gate walkthrough that touches the approval chain (gate rule 5), rather than
> carried as an open Critical.

> **§14.5 is SUPERSEDED BY OWNER DECISION, and it did its job.** The SPM's boundary — *"EP42 records that a
> step change happened at a review. It does not build the review."* — existed to stop performance management
> arriving **by accident**, inside an amendment, as a side-effect of a sentence about review timing. It did
> that, and it did not stop the owner choosing the scope **on purpose with the cost in front of him.** The
> boundary held until he spent it deliberately. That is the system working, not the ruling failing.
>
> **What still holds from §14.5:** **EP42 itself still does not build the review.** A step change in KAN-192
> records a `review_context` and a date and nothing more; the connection to a real review is one named seam,
> **KAN-236**. **UX §25's ban list and ADR-025's forbidden-column table stand unchanged and are now *more*
> load-bearing**, because performance management existing next door is precisely when somebody asks whether
> roadmap items can be ticked off.

**Depth:** outline only. EP44 is entering **S1 (requirements finalisation)**, not build. *"With all its
requirement"* means it gets the same full exercise EP42 got — SPM scope, BA acceptance criteria, Architect
technical design with engineer-level tasks, UX spec, UAT plan — but writing 500 acceptance criteria before the
epic outline has been agreed with the owner is how the last three amendments became expensive.

> **⚠ The two compliance items are DESIGN INPUTS carried as stories, not notes. This is the difference between
> EP44 being buildable in Germany and not.**
>
> **(1) EU AI Act / GDPR Art. 22 — Charter §1.** A full performance capability **with calibration**, feeding
> **pay**, is on the doorstep of *"a decision with legal or similarly significant effect"*. Nothing proposed
> here scores, ranks or auto-decides — **but calibration is exactly where forced distributions and ranked
> lists live**, and it is one plausible-sounding feature request away. So, as requirements: **KAN-232 is a
> story in the calibration wave, not an appendix** (human-in-the-loop attestation on every rating changed in
> calibration, an explainability record, and a hard rule that nothing is ranked or scored by the system and
> applied to a person) · **forced distribution is refused, not configurable** — distribution is **shown**
> (KAN-230) so a session can see its own shape, never **enforced**, because a configurable forced curve is an
> automated decision wearing a settings page · **bias testing is a story (KAN-240), not a launch task** —
> measure, report, **never auto-correct**. **Flagged for DPO/legal validation (Charter §9.7); nothing here is
> legal advice.**
>
> **(2) Works councils — OQ-8 escalates a third time and is now plausibly market-gating.** Performance
> management with calibration, feeding pay, across Germany and four Nordic countries — which is exactly where
> the seed data lives — is close to the definition of a co-determination matter. A launch consideration in A2,
> a design input in A3, **plausibly a gating dependency for those markets under A4.** The concrete
> consequence is **KAN-238**: the policy — the rating scale, the review forms, the calibration rules and the
> rating-to-pay mapping — must be **versioned, auditable and inspectable without exposing any individual's
> data**, because a council may need to review and agree it *before* the first cycle operates. **A launch
> blocker, not a build blocker**, and it belongs on the Customer-Readiness checklist.

**Three boundaries EP44 inherits and may not weaken:**

| # | Invariant | Why it is at risk in this epic |
|---|---|---|
| 1 | **The ladder is not a scoring instrument.** ADR-025's forbidden-column table and UX §25 stand unchanged — no rating, score, achievement, completion or progress column on `job_step_expectations` or `employee_step_roadmaps`. | With a performance surface next door, *"can we tick off roadmap items?"* stops being hypothetical. It is pre-refused in UX §25 and it will be asked anyway. |
| 2 | **Money never reaches `audit_log`** (D5.6 / amendment A-2), and a **rating** is treated with the same discipline as an amount. | A rating in an audit diff is readable by `audit_log:r` holders who are not entitled to it — the same routing-around problem that produced the money rule. |
| 3 | **Nothing scores, ranks or automatically decides.** A human enters a judgement; a company-configured mapping turns it into a number; a human approves the result. | The gate engages the moment anyone proposes a suggested rating, a ranked list, a forced distribution or any model output influencing pay — at which point it does not enter the backlog until it has full high-risk treatment. |

**Build order:** `P0 → P1 → P2 → P3 → P4 → P5`, with the compliance wave (P3) **inside** the build rather than
after it. **P3 gates P4's pay seam:** KAN-235 does not ship before KAN-232.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-219 | As a **customer admin**, I want to open a review cycle for a period, so performance conversations happen as a governed round rather than ad hoc. | A cycle is per company, per period, with a name, a window and a lifecycle `DRAFT → OPEN → IN_REVIEW → CALIBRATION → CLOSED`. One open cycle at a time per company. Registers the EP44 feature codes in **all four places** (`setup_db.py`, a migration, `seed_rbac.sql`, and default `role_feature_access` rows in both) — the DEF-004 rule. Company-scoped, audited at every transition, half-open effective dating per ADR-020. **Nothing about the cycle's content is predetermined**: the product ships no scale, no form, no rubric and no schedule. | Must · P2 |
| ⬜ KAN-220 | As **HR**, I want the cycle to know who is in it, so joiners, leavers and probationers are handled deliberately rather than by accident. | Eligibility per cycle: joiners after the window opens, leavers before it closes, part-cycle participants, employees with no manager, and `CONTRACTOR`/`INTERN` handling. **Every exclusion is counted and shown with its reason, never silent** — the same rule as compensation coverage. Company-scoped. | Must · P2 |
| ⬜ KAN-221 | As an **employee and my manager**, I want to agree what I am working towards this period, so the review has something concrete behind it. | Goal/objective authoring by employee and manager, per cycle, versioned. Optional cascade from a parent goal — **cascade is a link, never an automatic copy or an enforced target**. Row-scoped: a manager sees their direct reports' goals and nobody else's. Audited. | Must · P2 |
| ⬜ KAN-222 | As an **employee**, I want to record progress and check-ins during the period, so the review is not a memory test. | Narrative check-ins against a goal, timestamped, authored by either party, visible to both. **No score, no percentage complete, no RAG, no automatic status.** A completion percentage is a rating with a friendlier name and it is refused. | Must · P2 |
| ⬜ KAN-223 | As a **customer admin**, I want a library of goal templates we wrote ourselves, so managers are not starting from a blank page. | Company-authored templates, versioned. **Nothing predetermined and nothing suggested** — the product ships no example goals and no "typical" text (A3-1's discipline, extended: a suggested goal is a recommendation about somebody's job we have no basis for). | Should · P3 |
| ⬜ KAN-224 | As an **employee**, I want to write my own assessment before my manager writes theirs, so my view is on the record. | Self-assessment per cycle against the company's form. Visible to the manager on submission; **the manager's assessment is not visible to the employee until the cycle reaches its release point**, so a self-assessment is not anchored by a rating already given. Versioned; the employee may amend before submission and not after. | Must · P2 |
| ⬜ KAN-225 | As a **manager**, I want to assess each of my people against what we agreed, so the conversation is prepared and recorded. | Manager assessment per employee per cycle, row-scoped to direct reports. Cites the goals from KAN-221 and, where one exists, **the step roadmap from EP42's KAN-207** — the owner's own narrative link (*"the expectation from the employee is if they satisfy in next level the compensation review based on that"*) made visible rather than implied. Audited; versioned. | Must · P2 |
| ⬜ KAN-226 | As a **customer admin**, I want to define our rating scale, so the words mean what we mean by them. | Company-defined **ordinal** scale with authored labels and descriptions, **versioned** — a rating from 2027 must still be readable in 2029 against the scale that produced it. **Nothing predetermined, nothing suggested**: no shipped scale, no default point count, no "typical" wording. A company that has not authored a scale **cannot open a cycle**. | Must · P2 |
| ⬜ KAN-227 | As a **customer admin**, I want to define the review form, so it asks what we ask. | Company-authored sections and questions, versioned per cycle. Free-text, scale and goal-linked question types. **No scoring arithmetic across questions** — a weighted total is a computed rating, which is the thing KAN-232 gates. | Must · P2 |
| ⬜ KAN-228 | As an **employee**, I want the review conversation recorded honestly, so the record says what actually happened. | The conversation is recorded with a date and both parties. **The employee confirms the conversation happened; they do not "accept" a rating** — the button reads **`Confirm we discussed this`, never `Accept`**, and the displayed state is **`Discussed with Ravi on 14 March`, never "agreed"** (standing rule 6 — a label is a claim; recording "agreed" when somebody merely read it is a false record about a person). **A right of reply is mandatory, not optional** (KAN-234). Non-acknowledgement blocks nothing and is surfaced back to the manager. | Must · P2 |
| ⬜ KAN-229 | As **HR**, I want a calibration session where managers compare their assessments, so ratings mean the same thing across teams. | A calibration session is a **human forum**: a named group of employees, a named set of participants, a scheduled moment, and a record. Participants see the group's assessments side by side, row-scoped to the session's population. **The system convenes and records; it never proposes, orders or adjusts.** Audited. | Must · P2 |
| ⬜ KAN-230 | As **HR**, I want to see the shape of our ratings during calibration, so a session can see its own bias. | The distribution across the session's population is **shown** — counts per scale point, and a comparison against the company's other sessions. **Never enforced.** There is no target curve, no quota, no warning that a distribution is "wrong", and **no configuration option that would create one**: a configurable forced curve is an automated decision with significant effect wearing a settings page, and it is refused at the product level rather than left to a tenant. **No aggregate rendered below n = 5** (CFL-42-32 applies here exactly as it does to pay). | Must · P2 |
| ⬜ KAN-231 | As a **compliance owner**, I want every rating that calibration changed to say who changed it and why, so a decision about a person can be explained. | Every change to a rating inside calibration writes **actor, reason (mandatory), before → after, and the session it happened in**. The employee's own view (KAN-234) shows that a calibration adjustment occurred — **hiding it would make the record dishonest**, which is the same reasoning that gives the subject of a pay-equity finding read access without disposition controls. Append-only; no silent overwrite. | Must · P2 |
| ⬜ KAN-232 | As a **compliance owner**, I want the Art. 22 / EU AI Act gate built into the review rather than assessed after it, so we do not cross the line by increment. (**Charter §1 · A4 §4**) | **Human-in-the-loop attestation** on every rating that reaches a pay consequence: a named human confirms the decision, and the confirmation is the record. **An explainability record** per rating — the goals, the assessments and any calibration change that produced it, retrievable as one narrative for the subject. **A hard product rule, asserted by test: no ranking, score, index or model output is computed by the system and applied to a person.** No automated decision-making, no profiling, no algorithmic ranking anywhere in EP44. **The gate engages — and the story does not enter the backlog until it has full high-risk treatment — the moment anyone proposes a suggested rating, a ranked list, a forced distribution, or any model output influencing pay.** DPO/legal validation required before P4 ships. **Gates KAN-235.** | **Must · P1** |
| ⬜ KAN-233 | As **HR**, I want ratings history, and I want it visible only to the people entitled to it. | Ratings history per employee per cycle, retained and readable against **the scale version that produced it**. Its own feature code, row-scoped like pay, with **its own negative-visibility suite** asserting absence **from the payload** and not merely from the DOM — absent from the profile, the directory, the org tree, search, every export and every other feature's surface. **Cross-tenant subject ids return `404`, not `403`** (CFL-42-33's ruling, applied here from the start rather than retro-fitted). | Must · P2 |
| ⬜ KAN-234 | As an **employee**, I want to read my own review and say something back, so the record is not only my manager's version. | The employee sees their own assessment, their rating, and the fact of any calibration adjustment, **after the cycle's release point and not before**. **A right of reply, recorded alongside and never editable by the manager.** Plain language, no jargon, **no forward-looking language that reads as a promise** — the same discipline as "My Pay" and the top-step signal. | Must · P2 |
| ⬜ KAN-235 | As **HR**, I want the rating to feed the pay decision and nothing else, so a performance judgement does not leak into every other surface. (**the pay seam — EP43's KAN-216 reads this**) | **Single-purpose, enforced the way pay is:** written in a cycle, read by the pay cycle that consumes it, used for nothing else. Absent from the profile, the directory, the org tree, reporting and every export. Row-scoped, its own gate, its own negative-visibility assertions. **Blocked by KAN-232** — no rating reaches a pay consequence before the Art. 22 gate is in place. **Not shown to the employee as a pay input** — communicating a pay decision is a conversation, and the rating's route to money is EP43's, not a screen here. | Must · P2 |
| ⬜ KAN-236 | As a **manager**, I want a review to be the moment a step change is recorded, so EP42's `review_context` points at something real. (**the step seam**) | A closed review cycle becomes a selectable `review_context` for EP42's KAN-192 step change, with its date. **The pay proposal that follows cites the roadmap it fulfils** (EP42's KAN-207) — A2's narrative link, finally connected to a real review instead of a free-text context. **This does not make a step change automatic** and it does not make a review *required* for one: OQ-1 is closed — progression is a human decision — and the off-cycle context stays. **And it does not weaken A6:** the review justifies the **step**, the step determines the **base pay**, and nothing here lets a rating set an amount. | Must · P2 |
| ⬜ KAN-237 | As **HR leadership**, I want to know whether the cycle is actually happening, without seeing who scored what. | Completion and cycle-health reporting only — assessments submitted, conversations recorded, calibration sessions held, overdue counts. **No individual ratings, and no aggregate of any kind below n = 5** (CFL-42-32). Company-scoped; **cross-tenant aggregation of any kind is refused, including for SYSTEM_ADMIN.** | Should · P3 |
| ⬜ KAN-238 | As a **works-council representative or compliance owner**, I want to review the rules before they are applied to people, so consultation is possible. (**OQ-8, now a design input**) | The **policy** — the rating scale (KAN-226), the review forms (KAN-227), the calibration rules (KAN-229/230) and the rating-to-pay mapping (EP43's KAN-216) — is **versioned, auditable and inspectable without exposing any individual's data**. A named reviewer can read the whole policy for a period and see nothing about any person. **A launch blocker for the German and Nordic markets, not a build blocker**, and it goes on the Customer-Readiness checklist. Note the standing platform limitation (**CFL-42-22**): the access model still cannot express "read company-wide, write nothing", so a read-only reviewer has no clean grant. **This is the second epic to need it — if OQ-8 comes back "yes", that limitation stops being theoretical and gets its own decision.** | Must · P2 |
| ⬜ KAN-239 | As a **DPO**, I want to know what performance data we keep, for how long, and what erasure does to it. | Retention class and period for assessments, ratings, calibration records and check-ins, per company, reusing EP38's single retention clock (**one clock, not a second one** — OQ-BA-6's ruling). What erasure removes and what must survive, extending the BA's §4.7 enumeration the way CFL-42-3 extended it for pay — **and the same lesson applies: EP38's erasure list predates this data class and will be false the day EP44 lands.** DPIA items routed to the DPO list alongside DPO-1. **Nothing here is legal advice.** | Must · P2 |
| ⬜ KAN-240 | As a **compliance owner**, I want to know whether our ratings are biased, so we can look at it rather than assume. | Measure the rating distribution across the protected characteristics the tenant **lawfully** holds, per cycle, per level. **Report only — never auto-correct, never adjust a rating, never suggest one.** No aggregate below n = 5. **Blocked on the same purpose-limitation question as EP42's DPO-1**: holding a characteristic for one purpose does not make it lawful to process for this one. Runs **after** KAN-232, and it is a measurement, **not a compliance conclusion** — the same framing rule every pay-equity screen carries. | Should · P3 |

**Open items for the product owner / SPM:**

1. **The epic outline above needs the owner's confirmation before the full requirements exercise starts.** He
   asked for *"a detailed performance requirement implementation"* and he will get one — but the last three
   amendments cost what they cost because specification ran ahead of agreement on shape. **The shape is 22
   stories in six waves with the compliance gate inside the build; confirm, then specify.**
2. **OQ-8 (works councils) is now the highest-value unanswered question in the programme.** It was a launch
   consideration in A2, a design input in A3, and under A4 it is plausibly **market-gating** for Germany and
   the Nordics, where the seed data lives. Not a build blocker; **a launch blocker**, and discovering it during
   a rollout stops the rollout.
3. **EP44 does not start until EP42 W4 is complete**, and **EP43 does not start until EP44 is complete** —
   except KAN-211 and KAN-215, which have no performance dependency and may run in parallel if capacity allows
   (**a Delivery capacity call, not a dependency**). Nothing is blocked meanwhile: EP42's KAN-210 lets a
   company run a manual annual round today.

---

## EP43 — Annual Compensation Review Cycle  —  ⬜ Planned
**ID:** KAN-211 · **Label:** `compensation` `annual-cycle` `performance-input` `stage-S3`
**Source:** the product owner's **Amendment A2**, 2026-08-09 — *"for each year company defines its own hike
percentage for each based on market situation and their own income and performance of the employee"* — extended
by **Amendment A3**: *"Introduce performance input module with all it's requirement implement this first if
required if this the blocker"* and *"This will configuarable in Admin page by the employer and cannot be
predeterined."*
Business goal **BG7 — Pay decisions this company can defend**. Sibling of EP42, **sequenced after EP42 W4**.
**Description:** the second trigger for a pay change. EP42 covers pay moving because somebody's **job** changed
(a step or a level). EP43 covers pay moving because the **year** changed — an annual cycle in which the company
sets a hike percentage from market movement, its own income and each employee's performance, differentiates it
per person, approves it once, and applies it on an effective date.

> **Why this is a sibling epic and not EP42 W5** (SPM ruling, `EP42_SPM_SCOPE_AND_DECISIONS.md` §18.4):
> **(1)** EP42 is already 23 stories, 175 tasks, a 71-day critical path and ~14–16 calendar weeks, and it has
> been amended **twice in a single day**. A recurring annual process with a performance input would take it to
> ~28 stories and past the size defensible as one commitment — and the longer an epic runs, the more certain it
> is to be re-scoped mid-flight, which this one has already demonstrated. **(2)** It is a different shape of
> thing: EP42 is a data model and a check; this is a **business process** with a calendar, a budget, a
> differentiation round and a bulk approval — closer in shape to EP38's lifecycle workflows. **(3)** The split
> keeps **§14.5 true for EP42** (*"records that a step change happened at a review; does not build the review"*)
> and lets EP43 own its own explicit, narrow boundary decision on the performance input, instead of leaving that
> boundary ambiguous across 28 stories.
>
> **The one real counter-argument, and how it is answered.** Without re-basing, an annual hike degrades EP42's
> equity check. That coupling is genuine — so **the capability was separated from the process**: effective-dated
> pay points and the ladder re-base action are **KAN-206 and KAN-210, inside EP42**. A company can therefore
> re-base manually the day they grant a hike, with no cycle tooling at all. **EP42 shipping without EP43 is safe
> rather than degrading**, which is the only thing that made a W5 look necessary.
>
> **If S3 runs long, EP43 is the natural descope, and that is said now rather than negotiated later.** A first
> hike can be run with EP42's tools: re-base the ladder (KAN-210), adjust salaries through the import (KAN-195),
> approve through the existing chain. Laborious, and it works. **EP42 has no such fallback.**

**Build order:** `KAN-216 → KAN-211 → KAN-213 → KAN-214 → KAN-215`. **Five stories, reduced from seven by A6** — see the A4–A6 note below. **Sequenced last in the BG7 programme: EP42 → EP44 → EP43.**

**Depth:** outline only. EP43 is entering **S1 (requirements finalisation)**, not build. The stories below are
backlog-summary depth deliberately — writing 200 acceptance criteria for an epic that has not been scoped with
the owner is how the last two amendments became expensive.

> **⚠ AMENDMENT A3 — the owner authorised a performance module, which overturns SPM §14.5.** Recorded as
> **superseded by owner decision**, not quietly dropped: §14.5's reasoning was scope protection, it stopped
> performance management arriving *by accident* inside an amendment, and it did not stop the owner choosing that
> scope **on purpose with the cost visible**. That is a boundary working, not a ruling failing.
>
> **His phrase reads two ways and they are a quarter apart, so the choice goes back to him** (full sizing in
> `EP42_SPM_SCOPE_AND_DECISIONS.md` §21.2):
>
> | | Scope | Size | Where |
> |---|---|---|---|
> | **(a) performance *input*** — a manager-entered band per employee per cycle, feeding the hike and nothing else | **2 stories** — KAN-216, KAN-217 | ~2–3 weeks, **no delay** | **inside EP43, first** |
> | **(b) performance *management*** — cycles, goals, self-assessment, calibration, ratings history | **≈20–25 stories** | 12–16 weeks, and it goes **first**, so the hike cycle moves **~a quarter** | **EP44** |
>
> **SPM recommends (a), Confidence High**, and the team builds it meanwhile. The decisive argument is his own
> conditional — *"implement this first **if required if this the blocker**"*: under (a) nothing is blocked for
> more than a fortnight, whereas **(b) *becomes* the blocker he was trying to route around**. The noun is
> *input*; the context was a plumbing question about the hike calculation; and nobody has asked to *run* a
> performance review in this product. (a) is shaped so (b) extends it rather than replacing it.
>
> **Also settled by A3, and binding on every story below:** the hike policy is **employer-authored on an admin
> page with nothing predetermined** — no shipped percentage, band, multiplier or formula, **and no suggested
> value either** (a suggestion is a recommendation about somebody's pay that we have no basis for; same
> principle as "never derive, estimate or impute a salary"). A company that has not authored a policy **cannot
> open a cycle**.
>
> **The Charter §1 gate, stated so it is not crossed by increment:** nothing in EP43 **scores, ranks or
> automatically decides** anything about a person — a manager enters a band, a company-configured multiplier
> turns it into a number, a human approves the result. **The EU AI Act / GDPR Art. 22 gate engages the moment
> anyone proposes a suggested rating, a ranked list, a forced distribution, or any model output influencing
> pay**, and at that point it needs the full high-risk treatment before it enters the backlog.

> **⚠⚠ AMENDMENTS A4–A6 — this epic loses two stories and changes shape.** Full reasoning in
> `EP42_SPM_SCOPE_AND_DECISIONS.md` §22.11.2.
>
> **A6 collapsed EP43's central mechanism as well as EP42's, and it is the same collapse.** The per-employee
> annual hike percentage — A2-1's ruled default, *"a company guideline % per pay market, differentiated per
> employee, within a budget"* — was an artefact of the same wrong model, pay moving independently of the step.
> The owner has now said **"for each" means for each step transition**: *"from 2.0 to 2.1 the hike will be 2%
> this year while from 2.1 to 2.2 it will be 2.4"*. **Under A6 pay moves for exactly three reasons, and a
> discretionary per-person percentage is none of them:**
>
> | Reason pay moves | Where it lives |
> |---|---|
> | The step moved | **EP42** — KAN-192, at that transition's rate |
> | The ladder moved | **EP42** — KAN-210, and under A6 that **is** the act of granting the rise |
> | An exception, attributed | **EP42** — KAN-218, additional pay with a reason |
>
> **So EP43 is now a round-management epic, not a differentiation epic** — open a cycle, run the step reviews
> as a batch, approve once, apply on an effective date, close out and move the ladder. **KAN-212 is withdrawn
> (merged) and KAN-217 is withdrawn (superseded by EP44); seven stories become five.** Confidence
> **Medium-High**; the single thing being inferred is whether he still wants a discretionary percentage on top,
> and that is **Q3** on the owner's page with the default *no*.
>
> **And the sequencing changed.** The owner chose **full performance management** over the two-story input
> (A4 §4, A5 §2 — *"go ahead with full implemenation cycle as Product owneer accepting the delay"*), so
> **EP44 is a real epic and it goes ahead of this one**, honouring his *"implement this first if required if
> this the blocker"*. Programme order: **EP42 → EP44 → EP43.** **KAN-211 and KAN-215 have no performance
> dependency and may run in parallel with EP44's later waves if capacity allows** — that is a Delivery
> capacity call, not a dependency, and it is the answer to the question A4 §4 asked. **Nothing is blocked
> while EP44 runs:** KAN-210 lets a company run a manual annual round today, and that fallback is *stronger*
> under A6 than it was under A2, because moving the ladder now moves the money.

**Three invariants EP43 inherits from EP42 and may not weaken** — stated here because these are the ones that
get lost when a new epic starts:

| # | Invariant | Why it is at risk in this epic |
|---|---|---|
| 1 | **No pay change is applied without an approval a human gave**, and **KAN-198's four-eyes rule applies** — two different people, and the initiator may not approve. | A cycle cannot route 500 individual requests through the per-request chain; it needs a **cycle-level** approval. That is a legitimate different shape, and it is also exactly where the control quietly disappears if nobody names it. |
| 2 | **Money never reaches `audit_log`** (D5.6 / amendment A-2). | A cycle writing 500 compensation records writes **one correlated audit set with counts**, not 500 amounts. |
| 3 | **The budget is a warning, not a block.** | Blocking an over-budget distribution means the differentiation happens in a spreadsheet, which is the problem this product exists to end. Same reasoning as out-of-band pay in KAN-205. |

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-216 | As a **customer admin**, I want to define what our performance bands are and what each is worth, so the hike policy is ours and defensible. (**A3-2 option (a)** · **A3-1**) | Company-defined **ordinal bands** (e.g. below / meets / exceeds / outstanding), each mapping to a **configured multiplier** on the cycle guideline. Authored on an **admin page by the employer**, per company. **Nothing predetermined and nothing suggested** — no shipped band set, no shipped multipliers, no "typical is 3–5%" helper text, no placeholder. A company that has not authored a policy **cannot open a cycle**. **Versioned, auditable, and inspectable without exposing any individual's data** — because performance-related pay is works-council territory in Germany and the Nordics (where the seed data lives), and a works council may need to review and agree the bands *before* the cycle operates. That promotes **OQ-8 from a launch consideration to a design input**, and this requirement is where it lands. The *policy* of what "exceeds" is worth sits at company level; the *judgement* sits with the manager (KAN-217). **⚠ A4–A6 — re-pointed.** With full performance management chosen, this story is now the **rating → pay mapping**: company-defined multipliers against the ratings **EP44 produces**, rather than against a band typed in here. Everything else stands unchanged and is now more load-bearing, not less — **employer-authored, nothing predetermined and nothing suggested, versioned, auditable, and inspectable without exposing any individual's data**, because performance-related pay is works-council territory in Germany and the Nordics and a council may need to agree the mapping *before* the cycle runs (**OQ-8, now a design input**). | Must · P2 |
| ~~KAN-217~~ | ~~Per-employee performance input — a manager enters one band per employee per cycle.~~ | **⛔ WITHDRAWN — superseded by EP44.** This story *was* option (a): a manager typing a performance band into a pay screen. **The owner chose option (b), full performance management** (A4 §4, cost accepted verbatim in A5 §2), so the rating is now **produced by a review cycle in EP44** and read here rather than typed here. Recorded, not deleted: if EP44 is ever descoped, this is what comes back. | — |
| ⬜ KAN-211 | As a **customer admin**, I want to open an annual compensation cycle for a year, so pay reviews happen as a governed round instead of ad hoc. | A cycle is per company, per year, with a name, an **effective date** and a lifecycle `DRAFT → OPEN → APPROVED → APPLIED → CLOSED`. One open cycle at a time per company. Company-scoped, audited at every transition, gated on the compensation feature codes. Reuses EP42's effective-dating convention (ADR-020, half-open). | Must · P2 |
| ~~KAN-212~~ | ~~Set what funds the cycle and what differentiates it.~~ | **⛔ WITHDRAWN — merged, by A6.** Its *"market movement per pay market"* half **is** EP42's per-transition, per-year rate schedule (KAN-206) and the ladder re-base (KAN-210) — under A6, moving the ladder *is* granting the rise, so there is no separate funding number to author here. Its policy half is KAN-216. | — |
| ⬜ KAN-213 | As a **manager**, I want to distribute the cycle across my team, so the people who took on most get most. | Per-employee proposals generated from `current base × (1 + guideline × band multiplier)`; a manager worksheet showing a **running total against the budget**, over-budget **warned and reasoned, never blocked** (invariant 3). Row-scoped exactly as pay is — a manager proposes for their direct reports and sees nobody else's numbers. **⚠ A6 — re-specified.** This is no longer a **percentage-distribution** round. Under A6 pay moves for exactly three reasons — the step moved (at that transition's rate), the ladder moved, or an exception was **attributed as additional pay** — and a discretionary per-person percentage is none of them. The worksheet becomes a **step-movement and additional-pay round**: the manager proposes who moves a step and who needs a premium, row-scoped exactly as pay is, with the budget as a **warning, never a block** (invariant 3). *Whether he still wants a discretionary percentage on top is **Q3** on the owner's page (§22.13); the default being built is that he does not.* | Must · P2 |
| ⬜ KAN-214 | As **HR**, I want to approve the cycle once and have it apply, so 500 pay changes do not need 500 approvals. | **One cycle-level approval satisfying invariant 1** — two different people, the initiator excluded — then an atomic bulk apply on the effective date, each employee getting a normal EP42 compensation record so the timeline and the equity check see it as ordinary pay history. **One correlated audit set with counts** (invariant 2). Partial application is not a state that can exist. | Must · P2 |
| ⬜ KAN-215 | As a **customer admin**, I want closing the cycle to move the ladder too, so the fairness check still means something next year. | Close-out **re-bases the ladder by the market component**, using **KAN-210**'s capability, on the same effective date. Without this the check flags the whole workforce in the first cycle (**CFL-42-54**). Cycle history is retained and readable; a finding raised before the re-base still explains itself against the pay point in effect at its evaluation date. | Must · P2 |

**Open items for the product owner / SPM:**

1. **Five follow-ups on A2 are with the owner** — A2-1 (how much of the cycle is the system's job), A2-2 (the
   performance input, and the fact that it *is* a rating), A2-3 (does the cycle re-base the ladder — recommended,
   not optional), A2-4 (what the employee sees with level disclosure off), A2-5 (is a "position" a separate
   entity — no). All carry defaults the team builds against; the consolidated one-pager is
   `EP42_SPM_SCOPE_AND_DECISIONS.md` **§19**.
2. **"for each" in his sentence is ambiguous and has been ruled with a default** — a company guideline percentage
   per cycle **per pay market**, differentiated per employee by the performance band, within the budget the
   guideline implies. Confirmed as A2-1.
3. **EP43 does not start until EP42 W4 is complete**, and **it is the descope of choice** if S3 runs long.
