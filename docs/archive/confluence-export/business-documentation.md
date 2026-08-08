<!--
  FROZEN CONFLUENCE EXPORT — DO NOT EDIT.
  Source: https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/327683
  Page ID 327683 · last edited in Confluence 26 Apr 2026 · exported 8 Aug 2026.
  SUPERSEDED BY: docs/BUSINESS_DOCUMENTATION.md — read that instead.
-->

# HR Portal — Business Documentation

## 1. Purpose & Scope

The HR Portal is an internal web application that centralises employee management, organisational data, leave management, and workforce visibility across one or more companies. It serves HR administrators, line managers, and individual employees from a single unified system.

---

## 2. User Roles & Responsibilities

| Role | Who holds it | Scope | What they can do |
| --- | --- | --- | --- |
| **SYSTEM_ADMIN** (Tech Admin) | Platform / IT owner | **All companies** | Full access across every company; manages companies, all users, all roles; configures global settings; not affiliated with any company |
| **PORTAL_ADMIN** | HR Director / CTO of a company | **Own company only** | Full admin rights scoped to their company: manages employees, users, org structure, vacation types, branding; cannot see other companies data |
| **HR_ADMIN** | HR Manager / HR BP | Own company | Registers employees; manages directory; validates skills; runs reports |
| **SOLID_LINE_MANAGER** | Direct line manager | Own team | Views own team; approves/rejects vacation requests; sees org tree below them |
| **DOTTED_LINE_MANAGER** | Matrix / project manager | Dotted-line team | Same team views as solid-line manager |
| **DEPARTMENT_HEAD** | Head of a department | Own department | Views all employees in their department; directory access |
| **LOCATION_HEAD** | Office / site lead | Own location | Views employees at their location |
| **HIRING_MANAGER** | Recruiter / hiring lead | Assigned centre | Directory access for headcount context |
| **EMPLOYEE** | All portal users | Own profile | Views own profile; self-maintains skills and certifications; submits vacation requests |

A user may hold multiple roles simultaneously. Permissions are cumulative.

---

## 3. Key Business Processes

### 3.1 Employee Onboarding

**Trigger:** HR Admin or System Admin decides to add a new employee.

**Flow — 6-step registration form:**

1. **Personal Info** — name, email, phone, gender, job title, employment type, join date
2. **Employment** — auto-generated employee number, employment status
3. **Organisation** — assign to Business Unit, Functional Unit, Location, Cost Centre
4. **Reporting** — select Solid-Line and/or Dotted-Line manager
5. **Skills** — add skills with self-rating from a predefined catalogue
6. **Portal Access** — create login credentials and assign roles

System creates: employee record, org assignment, manager relationships, skills, user account, roles — all atomically.

**Business Rule:** Each employee belongs to exactly one company. Their location determines which location-specific vacation types they can access.

---

### 3.2 Vacation Request Workflow

**States:** PENDING → APPROVED or REJECTED, or PENDING → CANCELLED (by employee)

1. Employee submits request — status becomes PENDING
2. Manager sees request in Team Vacation → Pending tab; badge counter shown on My Team card
3. Manager approves or rejects with optional note
4. Employee sees updated status and manager note in request history

**Business Rules:**

* Employee cannot submit without a solid-line manager assigned
* Annual day limits enforced: PENDING + APPROVED days cannot exceed max_days_per_year
* Weekends excluded from working day counts
* Only PENDING requests can be cancelled or reviewed
* Manager ID recorded at submission; reassigning manager does not affect open requests

---

### 3.3 Vacation Type Configuration

**Who does it:** SYSTEM_ADMIN or PORTAL_ADMIN (for their company).

| Setting | Business Meaning |
| --- | --- |
| Company | Which company this type belongs to |
| Name + Colour | Display label and visual identifier |
| Max Days/Year | Annual entitlement cap; blank = unlimited |
| Paid / Unpaid | Whether the leave is compensated |
| Location scope | Empty = all locations; specify to restrict |
| Eligibility rules | Additional conditions (AND logic — all must pass) |

**Supported Eligibility Rules:** GENDER_EQ = FEMALE/MALE, MIN_TENURE_MONTHS = N, MIN_TENURE_YEARS = N

---

### 3.4 Skills Management

Employees self-rate skills at four levels: Beginner, Intermediate, Advanced, Expert. Admins and HR validate skills changing status from SELF_ASSESSED to VALIDATED. Validated skill data supports workforce planning, project staffing, and L&D gap analysis.

---

### 3.5 Organisational Hierarchy

```
Company
  └── Business Units (e.g. Technology & Innovation, Finance)
        └── Functional Units (e.g. Software Engineering, Data & AI)
  └── Locations (e.g. Stockholm HQ, Helsinki)
  └── Cost Centres (e.g. CC-TECH-001)
```

Each employee has a current org assignment. Reporting lines are maintained separately — an employee can have one solid-line (direct) manager and one dotted-line (matrix) manager.

---

### 3.6 Company Branding

| Feature | Admin sets | Employee sees |
| --- | --- | --- |
| Logo | Upload file or paste URL | Sidebar logo |
| Theme colour | Hex colour picker | All accent colours in company colour |
| Header banner | HTML content | Announcement bar above all pages |
| Footer | HTML content | Links bar below all pages |

Employees can independently choose light or dark mode saved to their account.

---

### 3.7 Two-Tier Administration Model

**Tech Admin (SYSTEM_ADMIN)** — owns the portal installation:

* No company affiliation (company_id = NULL)
* Sees all companies, all data simultaneously
* Can switch company context in the Admin Panel to manage one company at a time
* Manages platform-wide settings: widget refresh intervals, global role permissions, company creation

**Portal Admin (PORTAL_ADMIN)** — HR Director or CTO of a specific company:

* Belongs to exactly one company
* Administers that company autonomously: employees, org structure, vacation types, branding
* No visibility into other companies on the same portal
* Cannot assign SYSTEM_ADMIN or PORTAL_ADMIN roles to others

This supports a SaaS-style multi-tenancy model where one IT team operates the portal for multiple subsidiary companies, each self-managing their HR data independently.

---

### 3.8 Organisation Structure Administration

Portal Admins and Tech Admins manage org structure directly from the Admin Panel without SQL:

* **Business Units** — top-level units. Has name, optional code, description.
* **Locations** — physical/virtual offices. Has name, city, country, office code.
* **Functional Units** — sub-teams within a Business Unit.

Safety rule: Cannot delete an entry while employees are assigned to it (HTTP 409). Ownership rule: Portal Admin can only manage entries belonging to their own company (HTTP 403 otherwise).

---

### 3.9 Feature-Level Permission Control

A Roles & Permissions matrix in the Admin Panel (Tech Admin only) gives fine-grained control over what each role can do per feature area. Changes take effect immediately without restart. The SYSTEM_ADMIN row is always locked to full access.

Feature areas: Employee Profiles, Organisation Structure, User Accounts, Skills & Certifications, Vacations & Leave, Reports & Analytics, Company Settings, System Configuration.

---

## 4. Data Retention & Privacy Notes

| Data | Notes |
| --- | --- |
| Employee records | Retained regardless of employment_status |
| Vacation requests | Permanently retained with full audit trail |
| Uploaded logos | Previous file deleted when replaced |
| Theme preference | Stored per user account; not sensitive |
| Gender | Optional; used only for vacation eligibility filtering |

---

## 5. Metrics & Reporting

| Role | Metrics shown |
| --- | --- |
| SYSTEM_ADMIN / PORTAL_ADMIN | Total employees, active count, skill counts, certification counts |
| HR_ADMIN | Same as above |
| Manager | Own team headcount, team skills, team certifications |
| Employee | Own skills count, own certifications count, tenure |

---

## 6. Integration Points

| System | Status | Notes |
| --- | --- | --- |
| PostgreSQL | Live | All data; UUID primary keys |
| Jira | Live | 16 Epics · 80 Stories in KAN project |
| Confluence | Live | This documentation space |
| Email notifications | Not built | Recommended: notify on vacation approve/reject |
| Calendar integration | Not built | Recommended: iCal export of approved leave |
| SSO/LDAP | Not built | Recommended: replace email login with OAuth2/SAML |

GitHub: https://github.com/roysamiracc1-tech/employeemanagement
Jira Board: https://roysamiracc1-1777144763345.atlassian.net/jira/software/projects/KAN/boards

<!--
  ARCHIVIST'S NOTE (8 Aug 2026): the "Integration Points" table above claims Jira is Live with
  16 Epics / 80 Stories. That was false by the time of export — the KAN project contained zero
  issues. Preserved verbatim as the historical record.
-->
