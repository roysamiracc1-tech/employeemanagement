# HR Portal — Business Documentation

---

## 1. Purpose & Scope

The HR Portal is an internal web application that centralises employee management, organisational data, leave management, and workforce visibility across one or more companies. It is designed to serve HR administrators, line managers, and individual employees from a single unified system.

---

## 2. User Roles & Responsibilities

| Role | Who holds it | Scope | What they can do |
|------|-------------|-------|-----------------|
| **SYSTEM_ADMIN** (Tech Admin) | Platform / IT owner | **All companies** | Full access across every company; manages companies, all users, all roles; configures global settings; not affiliated with any company |
| **PORTAL_ADMIN** | HR Director / CTO of a company | **Own company only** | Full admin rights scoped to their company: manages employees, users, org structure, vacation types, branding; cannot see other companies' data |
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

**Flow:**
1. Admin navigates to **Admin Panel → Register New Employee**.
2. Completes 6 steps:
   - **Personal Info** — name, email, phone, gender, job title, employment type, status, join date
   - **Employment** — auto-generated employee number, employment status
   - **Organisation** — assign to Business Unit, Functional Unit, Location, Cost Centre
   - **Reporting** — select Solid-Line and/or Dotted-Line manager
   - **Skills** — add skills with self-rating from a predefined catalogue
   - **Portal Access** — create login credentials and assign roles
3. System creates: employee record → org assignment → manager relationships → employee skills → user account → user roles atomically.

**Business Rule:** Each employee must belong to exactly one company. Their location determines which location-specific vacation types they can access.

---

### 3.2 Vacation Request Workflow

**States:** `PENDING → APPROVED | REJECTED` or `PENDING → CANCELLED` (by employee)

```
Employee submits request
        │
        ▼
  Status: PENDING
  Manager sees in Team Vacation → Pending tab
  Badge counter shown on My Team card and Org Tree node
        │
        ├─ Manager clicks Approve (+ optional note)
        │       └─ Status → APPROVED
        │          Employee sees updated status in request history
        │
        └─ Manager clicks Reject (+ optional note)
                └─ Status → REJECTED
                   Employee sees manager note in request history
```

**Business Rules:**
- An employee **cannot** submit a request without a solid-line manager assigned.
- Annual day limits are enforced: PENDING + APPROVED days for the year cannot exceed `max_days_per_year` for that type.
- Weekends (Saturday, Sunday) are excluded from working day counts.
- Only `PENDING` requests can be cancelled by the employee or reviewed by the manager.
- Each request records the `manager_id` at submission time; reassigning a manager does not affect open requests.

---

### 3.3 Vacation Type Configuration

**Who does it:** SYSTEM_ADMIN only.

**Configuration options per type:**

| Setting | Business Meaning |
|---------|-----------------|
| Company | Which company this type belongs to |
| Name + Colour | Display label and visual identifier |
| Max Days/Year | Annual entitlement cap; blank = unlimited |
| Paid / Unpaid | Whether the leave is compensated |
| Location scope | Empty = available to all company locations; specify locations to restrict |
| Eligibility rules | Additional conditions an employee must meet (all must pass) |

**Supported Eligibility Rules:**

| Rule | Example Use Case |
|------|-----------------|
| `GENDER_EQ = FEMALE` | Maternity Leave — only visible to female employees |
| `GENDER_EQ = MALE` | Paternity Leave — only visible to male employees |
| `MIN_TENURE_MONTHS = 6` | Sick Leave — only after 6 months of employment |
| `MIN_TENURE_YEARS = 3` | Long Service Leave — only after 3 years |

Rules use **AND logic**: if a type has both a gender rule and a tenure rule, the employee must satisfy both.

---

### 3.4 Skills Management

**Self-assessment:** Employees add skills from the company catalogue and rate themselves using four proficiency levels:
- 🌱 Beginner
- 💡 Intermediate
- ⚡ Advanced
- 🏆 Expert

**Validation by manager/admin:**
- Admins or HR can validate a skill, changing its status from `SELF_ASSESSED` to `VALIDATED`.
- Validated skills show a green bar in the directory and profile; self-assessed skills show a blue bar.

**Business value:** Validated skill data supports workforce planning, project staffing, and L&D gap analysis.

---

### 3.5 Organisational Hierarchy

The portal models a four-level hierarchy per company:

```
Company
  └── Business Units (e.g. Engineering, Finance)
        └── Functional Units (e.g. Platform, Data Engineering)
  └── Locations (e.g. London HQ, Singapore Office)
  └── Cost Centres (e.g. CC-ENG-001)
```

Each employee has a current org assignment linking them to any combination of these levels.

**Reporting lines** are separate from org placement and are maintained in `manager_relationships`. An employee can have:
- One current **solid-line** (direct) manager
- One current **dotted-line** (matrix) manager

---

### 3.6 Company Branding

Each company can customise how the portal appears for their employees:

| Feature | Admin can set | Employee sees |
|---------|--------------|---------------|
| Logo | Upload file or paste URL | Sidebar logo instead of "HR" initials |
| Theme colour | Hex colour picker | All accent colours (buttons, links, nav) in company colour |
| Header banner | HTML content | Announcement bar above all pages |
| Footer | HTML content | Links bar below all pages |

Individual employees can also choose **light or dark mode** independently of company branding. This preference is saved to their account.

---

### 3.7 Two-Tier Administration Model

The portal distinguishes between **platform administration** and **company administration**:

**Tech Admin (SYSTEM_ADMIN)** — the person or team who owns the portal installation:
- Has no company affiliation. They are a super-user above the company layer.
- Can create and manage multiple companies on the same portal instance.
- Can switch company context in the Admin Panel to view and manage any specific company's data without logging out.
- When no company is selected ("All Companies"), they see data across every company simultaneously.
- Manages platform-wide settings: widget refresh intervals, global role permissions, company creation.

**Portal Admin (PORTAL_ADMIN)** — the HR Director, HRBP Director, or CTO of a specific company:
- Belongs to exactly one company.
- Administers that company autonomously: adds/removes employees, manages org structure, configures vacation types, sets company branding.
- Has no visibility into other companies registered on the same portal.
- Can assign any role *except* SYSTEM_ADMIN and PORTAL_ADMIN to employees within their company.

This model supports a **SaaS-style multi-tenancy** use case where one IT team operates the portal on behalf of multiple subsidiary companies, each of which manages its own HR data independently.

---

### 3.8 Organisation Structure Administration

Portal Admins and Tech Admins can manage the three-level org structure directly from the Admin Panel without writing SQL:

**Business Units** — top-level organisational units (e.g. Technology & Innovation, Finance). Each has a name, optional code, and description.

**Locations** — physical or virtual offices (e.g. Stockholm HQ, Helsinki). Each has a name, city, country, and an office code.

**Functional Units** — sub-teams within a Business Unit (e.g. Software Engineering within Technology). Each links to a parent BU.

**Safety rule:** An entry cannot be deleted while employees are assigned to it. The system shows a 409 error with the count of currently assigned employees.

**Ownership rule:** Portal Admin can only add, edit, and delete entries belonging to their own company. Attempting to modify another company's record returns HTTP 403.

---

### 3.9 Feature-Level Permission Control

A **Roles & Permissions matrix** in the Admin Panel (Tech Admin only) allows fine-grained control over what each role can do per feature area:

| Feature Area | Read | Write | Delete |
|--------------|------|-------|--------|
| Employee Profiles | Can view | Can update records | Can remove records |
| Organisation Structure | Can view BU/loc/FU | Can add/edit | Can delete |
| User Accounts | Can view | Can create/disable | Can remove |
| Skills & Certifications | Can view | Can validate/edit | Can remove |
| Vacations & Leave | Can view requests | Can approve/configure | Can cancel/delete |
| Reports & Analytics | Can view dashboards | — | — |
| Company Settings | Can view branding | Can update branding | — |
| System Configuration | Can view settings | Can update settings | — |

Changes take effect immediately without a restart. The `SYSTEM_ADMIN` row is always locked to full access and cannot be reduced.

---

## 4. Data Retention & Privacy Notes

| Data | Notes |
|------|-------|
| Employee records | Retained regardless of `employment_status`; exit date recorded on departure |
| Vacation requests | Permanently retained with full audit trail (status, manager note, review timestamp) |
| Uploaded logos | Stored in `static/uploads/logos/`; previous file is deleted when replaced |
| Theme preference | Stored per user account; not sensitive |
| Gender | Optional field; used only for vacation eligibility filtering; stored as `MALE/FEMALE/OTHER` |

---

## 5. Metrics & Reporting

The dashboard provides real-time counts for key operational metrics. These differ by role:

| Role | Metrics shown |
|------|--------------|
| SYSTEM_ADMIN | Total employees, active employees, skill counts, certification counts (company-wide) |
| HR_ADMIN | Same as above |
| Manager | Own team headcount, team skills, team certifications |
| Employee | Own skills count, own certifications count, tenure |

Counts are refreshed on a configurable per-role interval (default varies; configurable by SYSTEM_ADMIN).

---

## 6. Integration Points (Current & Recommended)

| System | Status | Notes |
|--------|--------|-------|
| PostgreSQL | Live | All data stored; UUID primary keys throughout |
| Flask static file serving | Live | Logo uploads served from `/static/uploads/logos/` |
| Google Fonts (Inter) | Live | Loaded from CDN in `base.html` |
| Email notifications | Not built | Recommended: send email to employee when vacation is approved/rejected |
| Calendar integration | Not built | Recommended: iCal export of approved leave dates |
| HRIS import/export | Not built | Recommended: CSV import for bulk employee creation |
| SSO/LDAP | Not built | Recommended: replace email-only login with OAuth2/SAML |

