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

### 3.10 Org Tree — Family Tree View

The **Organisation Tree** page is accessible to every logged-in employee. It renders as a visual **family tree** (top-down, hierarchical) rather than a folder/indent list.

**How it works:**
- The tree always **starts from the logged-in employee** — they appear at the root with their team fanning out below.
- Each person is shown as a card with their avatar, name, job title, and location.
- Solid-line reporting relationships are shown as connecting lines between cards.

**Navigation:**

| Action | How |
|--------|-----|
| Move **up** to manager | Click the blue **↑ [Manager Name]** button above the tree |
| Move **down** into a team | Click the **Focus ↓** magnifier on any card with reports |
| Jump to any level | Click a name in the **breadcrumb trail** at the top |
| Return to own view | Click **← My view** when browsing elsewhere in the org |
| Expand / collapse a team | Click the pill counter (e.g. **▾ 4**) below any card |

**Access:** All roles (including individual contributors) can view the org tree. Everyone always starts from their own node and can navigate upwards to see the full company hierarchy.

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


---

### 3.11 Email Notifications

All HR events trigger email notifications to relevant parties. Notifications are configurable per company by Company Admin or Super Admin.

**Notification events:**

| Event | Default recipients |
|---|---|
| `VACATION_REQUESTED` | Solid-Line Manager (forced), HR Admin (mutable) |
| `VACATION_APPROVED` | Employee (mutable) |
| `VACATION_REJECTED` | Employee (forced) |
| `VACATION_CANCELLED` | Manager + HR Admin (mutable) |
| `EMPLOYEE_CREATED` | HR Admin + Solid-Line Manager (mutable) |
| `SKILL_VALIDATED` | Employee (mutable) |

**Configuration (Admin Panel → Notifications tab):**
- Enable or disable each event per recipient role
- Mark `allow_mute = false` to prevent recipients from silencing a critical notification
- "Inherit to sub-roles" propagates settings down the role hierarchy in one click
- Individual users can mute mutable notifications from their profile preferences

---

### 3.12 Full-text Employee & Vacation Search

A global search bar is available in the topbar on every page and a dedicated search results page at `/search`.

**What can be searched:**
- **Employees** — name, job title, email, department (PostgreSQL GIN full-text index)
- **Vacations** — natural language: "my upcoming vacation", "team vacation next month"
- **Org chart** — natural language: "people reporting to me", "my team" → loads org tree

**How it works:**
- A database trigger (`trg_employee_search`) keeps the `employee_search_index` table updated automatically whenever an employee record is inserted or changed.
- Vacation queries are matched against pattern libraries and translated to date-range SQL.
- Org chart queries detect intent ("reporting", "team") and return an action shortcut that links directly to the org tree focused at the right person.

---

### 3.13 Vacation Calendar

All employees have access to a month-grid leave calendar at `/vacation/calendar`.

**Scope filters:**
- **Mine** — own approved and pending requests
- **My Team** — direct solid-line reports' approved and pending requests
- **All** — company-wide (scoped to user's company)

Weekend days are greyed out. Pending requests show with a hatched pattern. A colour legend is auto-generated from the vacation type colours configured by the company.

---

### 3.14 Bulk Employee Import

Company Admins and HR Admins can import employees in bulk via CSV.

**Workflow:**
1. Admin uploads a CSV file (drag-and-drop or browse). Required columns: `first_name`, `last_name`, `email`.
2. System validates each row: required fields, email format, uniqueness, employment type enum.
3. A preview shows all rows with per-row validation status and error messages.
4. **Portal Admin / Tech Admin**: zero-error imports are auto-approved and can be processed immediately.
5. **HR Admin**: imports go to `PENDING_REVIEW` status and require Company Admin approval before processing.
6. Once approved, clicking "Process Import" creates all valid employee records.
7. Failed rows are marked `SKIPPED`; the import is marked `COMPLETED` even if some rows fail.

**CSV format:** `first_name`, `last_name`, `email` (required) + `job_title`, `employment_type`, `gender`, `phone_number`, `join_date` (optional).

---

### 3.15 Mobile Responsive Design

The portal is fully usable on mobile devices (phones and tablets).

| Breakpoint | Behaviour |
|---|---|
| < 768px | Sidebar becomes an off-canvas drawer (hamburger opens, tap overlay closes) |
| < 768px | Data tables convert to labelled card stacks |
| < 768px | Admin tabs stack vertically |
| < 768px | Login panels stack vertically |
| < 480px | Search bar hidden from topbar (use /search page) |
| All sizes | Org tree is horizontally scrollable with touch momentum |
