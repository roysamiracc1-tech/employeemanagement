# HR Portal — Business Overview, Features & Access Rights

> **Source:** promoted from the Confluence page *"HR Portal — Business Overview, Features & Access Rights"*
> (v1.1, last edited 18 May 2026) during the 8 Aug 2026 migration off Atlassian. This is now the
> living copy — edit it here, in git. See [`project-management/README.md`](project-management/README.md).
>
> Companion documents: [`BUSINESS_DOCUMENTATION.md`](BUSINESS_DOCUMENTATION.md) (processes and business
> rules) and [`TECHNICAL_DOCUMENTATION.md`](TECHNICAL_DOCUMENTATION.md) (implementation).

---

## 1. Executive Summary

The HR Portal is a multi-tenant, role-based HR management platform designed to give organisations a single source of truth for employee data, skills, leave management, and workforce analytics. The platform supports multiple companies under one deployment, with each company having its own isolated data, branding, and configurable feature set.

The system is built with a **two-tier permission architecture**:

* **Super Admin (System Admin)** sets global role capabilities across all companies
* **Company Admin (Portal Admin)** fine-tunes access within their own company for roles below them

---

## 2. Application Architecture Summary

| Layer | Technology |
| --- | --- |
| Backend | Python / Flask |
| Database | PostgreSQL |
| Frontend | Server-side Jinja2 templates + vanilla JS + Chart.js |
| Auth | Session-based with role arrays stored server-side |
| Deployment | Single-server, multi-company (multi-tenant) |

---

## 3. User Roles & Hierarchy

Roles are hierarchical. A role can only manage roles below it in the hierarchy.

```
SYSTEM_ADMIN
  └── PORTAL_ADMIN (Company Admin)
        ├── HR_ADMIN
        │     └── EMPLOYEE
        ├── DEPARTMENT_HEAD
        │     ├── LOCATION_HEAD
        │     ├── SOLID_LINE_MANAGER
        │     │     ├── DOTTED_LINE_MANAGER
        │     │     └── EMPLOYEE
        │     └── EMPLOYEE
        ├── HIRING_MANAGER
        │     └── EMPLOYEE
        └── EMPLOYEE
```

### Role Descriptions

| Role | Description |
| --- | --- |
| **SYSTEM_ADMIN** | Super admin. Full access to all companies, all features, all data. Manages global role-feature permissions and company feature toggles. |
| **PORTAL_ADMIN** | Company Admin. Full access within their company. Can configure which roles below them have access to specific features. |
| **HR_ADMIN** | HR Administrator. Manages employees, skills, vacations, and reports for the full organisation. |
| **DEPARTMENT_HEAD** | Manages a business unit / department. Sees employees and data within their department. |
| **LOCATION_HEAD** | Manages a physical office location. Sees employees at their location. |
| **SOLID_LINE_MANAGER** | Direct line manager. Sees their recursive solid-line reporting subtree. |
| **DOTTED_LINE_MANAGER** | Indirect/matrix manager. Sees their direct dotted-line reports. |
| **HIRING_MANAGER** | Hiring-focused role. Sees their direct reports only. |
| **EMPLOYEE** | Standard employee. Sees own profile, own vacation requests, org tree, and public directory (where permitted). |

---

## 4. Portal Features

### 4.1 Feature Catalogue

| Feature Code | Feature Name | Description |
| --- | --- | --- |
| `employee_profiles` | Employee Profiles | View and manage employee personal, role and org data |
| `org_structure` | Organisation Structure | Manage business units, locations and functional units |
| `user_accounts` | User Accounts | Create, enable/disable and assign roles to portal users |
| `skills` | Skills & Certifications | View, validate and manage skill profiles |
| `vacations` | Vacations & Leave | Manage vacation types, entitlements and leave requests |
| `reports` | Reports & Analytics | Access competency dashboards and analytics |
| `company_settings` | Company Settings | Edit company branding, logo, theme and metadata |
| `system_config` | System Configuration | Widget settings and global platform configuration |
| `skills_intelligence` | Skills Intelligence | Benchmark company skills against industry trends (SO 2025) |
| `org_change` | Position Change Workflow | Drag-and-drop employee moves with sequential multi-level approval |

### 4.2 Default Role → Feature Access Matrix

✅ = Enabled by default    ❌ = Not enabled (can be granted by System Admin)

| Feature | SYSTEM_ADMIN | PORTAL_ADMIN | HR_ADMIN | DEPT_HEAD | LOCATION_HEAD | SOLID_LINE_MGR | DOTTED_LINE_MGR | HIRING_MGR | EMPLOYEE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Employee Profiles | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Org Structure | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| User Accounts | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Skills | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Vacations | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Reports & Analytics | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Company Settings | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| System Config | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Skills Intelligence | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

> **Note:** System Admin always has full access regardless of the matrix. Matrix values are the defaults seeded on setup; System Admin can change any cell via the Roles & Permissions tab.
>
> **Verify before relying on this table.** It is a point-in-time snapshot of the seeds in `setup_db.py`;
> the database is the authority. The `org_change` defaults are not captured above — see
> [`TECHNICAL_DOCUMENTATION.md`](TECHNICAL_DOCUMENTATION.md) §22.

---

## 5. Permission System Architecture

### 5.1 Two-Tier Permission Model

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: role_feature_access  (Global — set by SYSTEM_ADMIN) │
│  Which roles are ELIGIBLE for each feature across ALL        │
│  companies. This is the ceiling — Portal Admin cannot grant  │
│  access beyond what System Admin allows here.               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: company_role_feature_access  (Per-Company)          │
│  Portal Admin can ENABLE or DISABLE eligible roles for their │
│  company. Only roles below PORTAL_ADMIN in the hierarchy     │
│  can be toggled. Changes affect only their company.          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Access Check Logic

When any user attempts to access a feature:

1. **Login required** — session must be active
2. **Role-feature access** — user's role(s) must have `can_read = true` in `role_feature_access` (global ceiling)
3. **Company override** — if a `company_role_feature_access` row exists for this company + role + feature, it is applied (can restrict below the global default)
4. **Company feature toggle** — for premium features (Analytics, Skills Intelligence), the feature must be enabled for the company in `company_features`
5. **SYSTEM_ADMIN bypass** — always passes all checks automatically

### 5.3 Where Permissions Are Configured

| Who | Where | Controls |
| --- | --- | --- |
| SYSTEM_ADMIN | Admin Panel → **Roles & Permissions** tab | Global role → feature access matrix (R/W/D per role per feature) |
| PORTAL_ADMIN | Admin Panel → **Feature Access** tab | Per-company role toggles (on/off, constrained to roles below them) |
| SYSTEM_ADMIN | Companies page → feature toggles | Whether a premium feature is enabled for a specific company at all |

---

## 6. Feature Details

### 6.1 Employee Profiles

Allows authorised roles to view, create, and edit employee records.

**What's included:**

* Personal information (name, email, job title, employment type)
* Organisational assignment (business unit, location, functional unit)
* Manager relationships (solid-line and dotted-line)
* Skills & certifications
* Vacation history

**Access by operation:**

| Operation | Roles |
| --- | --- |
| View own profile | All roles |
| View other employees | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN, DEPARTMENT_HEAD, LOCATION_HEAD, HIRING_MANAGER |
| View own team | SOLID_LINE_MANAGER, DOTTED_LINE_MANAGER |
| Create / Edit employee | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN, SOLID_LINE_MANAGER (own team) |
| Delete employee | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |

---

### 6.2 Skills & Certifications

Tracks employee skill profiles with self-assessment and manager validation.

**Key concepts:**

* Employees self-assess proficiency (Beginner → Expert) and years of experience
* Managers validate or override proficiency levels
* Validation status: `SELF_ASSESSED` → `PENDING_MANAGER_VALIDATION` → `VALIDATED` or `REJECTED`
* Primary skills can be flagged

**Access by operation:**

| Operation | Roles |
| --- | --- |
| View own skills | All roles |
| Add/edit own skills | All roles (EMPLOYEE self-service) |
| View team skills | SOLID_LINE_MANAGER, DOTTED_LINE_MANAGER, DEPARTMENT_HEAD, HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |
| Validate / override skill level | SOLID_LINE_MANAGER, HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |
| Delete skill entry | Own entry: any role. Others: HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |

---

### 6.3 Vacations & Leave

Full leave management including request, approval, and tracking.

**Features:**

* Multiple vacation types (Annual, Sick, Parental, etc.) per company
* Location-based entitlements
* Approval workflow (employee → manager → HR)
* Team calendar view
* Notifications on submit, approve, reject, and cancel

**Access by operation:**

| Operation | Roles |
| --- | --- |
| View own vacation requests | All roles |
| Submit vacation request | EMPLOYEE, all roles |
| Approve / reject requests | SOLID_LINE_MANAGER, DOTTED_LINE_MANAGER, HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |
| Manage vacation types | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |
| View team vacation calendar | SOLID_LINE_MANAGER, DOTTED_LINE_MANAGER, HR_ADMIN, SYSTEM_ADMIN |

---

### 6.4 Organisation Structure

Manage the hierarchical structure of the company.

**Features:**

* Business units (departments)
* Locations (offices)
* Functional units (cross-functional teams)
* Org tree visualisation (interactive)
* Bulk import via CSV

**Access:**

| Operation | Roles |
| --- | --- |
| View org tree | All roles |
| View employee directory | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN, DEPARTMENT_HEAD, LOCATION_HEAD, HIRING_MANAGER |
| Create / edit org units | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |
| Manage locations | HR_ADMIN, PORTAL_ADMIN, SYSTEM_ADMIN |

**Employee Directory — Super Admin behaviour:** When SYSTEM_ADMIN selects a company via the company picker on the Employee Directory page, the directory, department filter, and location filter all scope to that company. The picker uses the same design as the Dashboard and Admin Panel (ctx-bar + co-picker dropdown with logo support).

---

### 6.5 Reports & Analytics

Data-driven dashboards for workforce intelligence.

**⚠️ Data scoping rule:** Manager-level roles see only data for their team. HR Admin and above see full-organisation data. A purple **"Your Team View"** banner appears when data is scoped.

**Tabs & metrics:**

| Tab | What it shows |
| --- | --- |
| **Overview** | Page views, active users, feature adoption, bulk import history |
| **Vacations** | Leave utilisation, pending approvals, type breakdown, department patterns |
| **Skills** | Coverage %, top skills, validation rates, avg years of experience |
| **Org Chart** | Headcount by dept/location, reporting depth, manager ratios |
| **Search** | Search query analysis (what employees search for) |

**Data scope by role:**

| Role | Sees |
| --- | --- |
| SYSTEM_ADMIN | Any selected company (full org) |
| PORTAL_ADMIN | Full organisation |
| HR_ADMIN | Full organisation |
| SOLID_LINE_MANAGER | Their recursive solid-line subtree |
| DOTTED_LINE_MANAGER | Their direct dotted-line reports |
| DEPARTMENT_HEAD | All employees in their business unit |
| LOCATION_HEAD | All employees at their location |
| HIRING_MANAGER | Their direct solid-line reports |

> **Company prerequisite:** The `reports` feature must be enabled for the company by SYSTEM_ADMIN before non-SA roles can access Analytics.

---

### 6.6 Skills Intelligence

Benchmarks company skill adoption against the **Stack Overflow 2025 Developer Survey**, providing data-driven insights for hiring and training decisions.

**⚠️ Data scoping rule:** Same team-scoping rules as Analytics apply to manager roles.

**Tabs & what they measure:**

| Tab | Metric | How measured | Key inference |
| --- | --- | --- | --- |
| **Gap Analysis** | Skill adoption vs SO 2025 benchmark | Gap = Industry % − Company %. Red = lag, Green = lead | Gaps >10pp → urgent training/hiring priority |
| **Proficiency Heatmap** | Depth of skill knowledge | Stacked bar of proficiency levels (Beginner→Expert) per top skill | Beginner-heavy bars = knowledge depth risk |
| **Trend Alignment** | Skills the industry wants to learn next | Scatter plot: X = company adoption, Y = industry desire. Four quadrants: Invest / Leverage / Monitor / Maintain | 🚀 Invest quadrant = highest strategic priority |
| **Category Coverage** | Breadth across tech domains | Coverage % = employees with ≥1 skill in domain ÷ total headcount | Narrow radar = over-specialised team |
| **By Job Title** | Skills coverage per role | Coverage % per job title | <30% coverage = data quality issue |
| **Validation** | Data quality & growth | Validated vs self-assessed ratio; monthly skill entry growth | Target: >50% validated for reliable decisions |

**Access prerequisites:**

1. Role must have `skills_intelligence` access in the global matrix (SYSTEM_ADMIN controls)
2. Company must have Skills Intelligence enabled (toggle in Companies page)
3. Company Admin can further restrict/grant per role via the Feature Access tab

---

### 6.7 Admin Panel

Central administration hub for PORTAL_ADMIN, HR_ADMIN, and SYSTEM_ADMIN.

**Tabs available:**

| Tab | Visible To | Purpose |
| --- | --- | --- |
| Users & Roles | PORTAL_ADMIN, HR_ADMIN, SYSTEM_ADMIN | Create users, assign roles, activate/deactivate accounts |
| Employees | PORTAL_ADMIN, HR_ADMIN, SYSTEM_ADMIN | Register and manage employee records |
| Organisation | PORTAL_ADMIN, HR_ADMIN, SYSTEM_ADMIN | Manage BUs, locations, functional units |
| Company Roles | PORTAL_ADMIN, SYSTEM_ADMIN (when company selected) | Create and manage company-specific roles |
| Roles & Permissions | **SYSTEM_ADMIN only** (no company selected) | Global role → feature access matrix (R/W/D per role per feature) |
| Feature Access | PORTAL_ADMIN, SYSTEM_ADMIN | Per-company role access overrides |
| Widget Settings | **SYSTEM_ADMIN only** | Dashboard auto-refresh intervals per role |

---

## 7. Navigation by Role

What each role sees in the sidebar navigation:

| Nav Item | SYSTEM_ADMIN | PORTAL_ADMIN | HR_ADMIN | DEPT_HEAD | SOLID_LINE_MGR | EMPLOYEE |
| --- | --- | --- | --- | --- | --- | --- |
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Employee Directory | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| My Team | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Org Tree | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vacation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Team Vacation | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Leave Calendar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bulk Import | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| My Company | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Admin Panel | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Vacation Types | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Companies | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tech Benchmarks | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Analytics | Configurable | Configurable | Configurable | Configurable | Configurable | ❌ |
| Skills Intelligence | Configurable | Configurable | Configurable | Configurable | Configurable | ❌ |

> **Configurable** = visible if role has `reports` / `skills_intelligence` access in the permissions matrix (set by System Admin and overridable per company by Portal Admin).

---

## 8. Multi-Tenant Architecture

### 8.1 Company Isolation

* Every employee, vacation request, skill entry, and org unit is scoped to a `company_id`
* SYSTEM_ADMIN can switch company context via a dropdown (they are not bound to any company)
* All other roles are strictly bound to their own company's data
* The company picker appears on Dashboard, Admin Panel, and Employee Directory — consistent design across all pages

### 8.2 Company Feature Toggles

Premium features can be enabled/disabled per company by SYSTEM_ADMIN:

| Feature | Toggle Location |
| --- | --- |
| Reports & Analytics | Companies page → feature toggle |
| Skills Intelligence | Companies page → feature toggle |

### 8.3 Per-Company Branding

Each company can have:

* Custom logo
* Custom theme colour (applied to sidebar and primary buttons)
* Custom company name in header

---

## 9. Key Business Rules

1. **SYSTEM_ADMIN has no company boundary.** They see all data and manage all companies. They are not assigned an employee record within any company.
2. **PORTAL_ADMIN cannot grant access beyond what SYSTEM_ADMIN allows.** If SYSTEM_ADMIN disables a role for a feature globally, Portal Admin cannot re-enable it for their company.
3. **Route guards use** `@require_feature_access`, never hardcoded role lists. This ensures that granting a role access in the permissions matrix takes effect immediately without code changes.
4. **Manager roles always see scoped data.** Analytics and Skills Intelligence data for managers is filtered to their team automatically. Managers cannot see organisation-wide data regardless of what features they have access to.
5. **Skills validation is manager-driven.** Self-assessed skills are marked as such and have lower trust. Manager-validated skills are the reliable signal for strategic workforce decisions. Target: >50% validation rate.
6. **Vacation approvals follow the solid-line hierarchy.** Leave requests go to the solid-line manager first. HR Admin can approve for any employee.
7. **Company features must be enabled before role access matters.** Even if a role has Skills Intelligence access in the permissions matrix, they cannot access it unless the company has the feature enabled via the company toggle.
8. **An employee can never initiate their own position change.** See the `org_change` invariants in `CLAUDE.md` and [`TECHNICAL_DOCUMENTATION.md`](TECHNICAL_DOCUMENTATION.md) §22.

---

## 10. Database Key Tables

| Table | Purpose |
| --- | --- |
| `companies` | One row per tenant company |
| `employees` | Employee records (scoped to company) |
| `users` | Login accounts linked to employees |
| `roles` | Role definitions (company_id = NULL for system roles, UUID for company-specific) |
| `portal_features` | Feature catalogue |
| `role_feature_access` | Global role → feature permissions (R/W/D) — set by SYSTEM_ADMIN |
| `company_role_feature_access` | Per-company role → feature overrides — set by PORTAL_ADMIN |
| `company_features` | Whether a premium feature is enabled for a company |
| `skills` | Skill catalogue |
| `employee_skills` | Employee skill entries with proficiency and validation status |
| `manager_relationships` | Solid-line and dotted-line manager links |
| `vacation_requests` | Leave requests with status and approval trail |
| `employee_org_assignments` | Employee → BU / location / functional unit mappings |
| `survey_benchmarks` | Stack Overflow 2025 survey data for Skills Intelligence benchmarking |

---

## 11. Quality & Test Coverage

The application has an automated test suite enforced via a pre-commit hook, plus two standalone
headless browser regression suites.

| Suite | How to run |
| --- | --- |
| Unit / route tests | `python -m pytest -q` |
| Browser regression | `python tests/ui/test_browser.py` |
| Vacation workflow regression | `python tests/ui/test_vacation_workflow.py` |

> Counts are deliberately not restated here — they change every release and go stale fast.
> Run the suites for current numbers. See `CLAUDE.md` for the mandatory pre-confirmation checklist.

**Test categories:**

* Access matrix: every route × every role
* Feature permission matrix: feature × role × R/W/D
* API input validation: all endpoints with bad inputs
* Auth comprehensive: UUID validation, feature access combos
* Company scoping: cross-tenant isolation tests
* Business logic: vacation rules, tree construction, helpers
* Session state: multi-role combinations, company context

---

## 12. Changelog

Entries below were carried over from Confluence. Ongoing changes are tracked in git history and in
[`project-management/BACKLOG.md`](project-management/BACKLOG.md).

| Date | Change |
| --- | --- |
| 8 Aug 2026 | **Migrated off Atlassian.** Confluence pages exported to `docs/`; Jira board (empty) retired; backlog moved to `docs/project-management/BACKLOG.md`. |
| 18 May 2026 | Test suite substantially expanded — new parametrized files covering access matrix, permission matrix, input validation, scoping, business logic, and session states. |
| 18 May 2026 | **6 input validation bugs fixed:** `api_update_roles`, `api_toggle_user`, `api_company_roles` create/update, `api_org_bu` create/update, `api_org_loc` create/update, `api_org_bu/loc` delete — all now return 400 instead of crashing on unexpected input types. |
| 18 May 2026 | **Employee Directory company picker** — Super Admin now has a `ctx-bar` + `co-picker` dropdown on the Employee Directory page matching the Dashboard and Admin Panel design. |
| 14 May 2026 | Manager-scoped analytics and Skills Intelligence — managers see team-only data |
| 14 May 2026 | Feature Access tab in Admin Panel — Portal Admin can configure per-company role access |
| 14 May 2026 | `role_feature_access` now actively enforces access (routes use `@require_feature_access`) |
| 14 May 2026 | Skills Intelligence added to `portal_features` — fully configurable like all other features |
| 14 May 2026 | Removed legacy `enabled_for_hr` flag — HR_ADMIN access controlled via permissions matrix |
| 14 May 2026 | Tab descriptions and info icon tooltips added to Skills Intelligence |
| 13 May 2026 | Skills Intelligence redesigned to match app design system |
| 13 May 2026 | Roles & Permissions — Save Changes button with unsaved highlight and confirm modal |

---

_Repository:_ https://github.com/roysamiracc1-tech/employeemanagement
