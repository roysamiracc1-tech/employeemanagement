# HR Portal — Business Documentation

---

## 1. Purpose & Scope

The HR Portal is an internal web application that centralises employee management, organisational data, leave management, and workforce visibility across one or more companies. It is designed to serve HR administrators, line managers, and individual employees from a single unified system.

---

## 2. User Roles & Responsibilities

| Role | Who holds it | What they can do |
|------|-------------|-----------------|
| **SYSTEM_ADMIN** | IT / Platform admin | Full access; registers companies and vacation types; manages all users and roles; configures branding and refresh settings |
| **HR_ADMIN** | HR Manager / HR BP | Registers employees; manages directory; validates skills; runs reports |
| **SOLID_LINE_MANAGER** | Direct line manager | Views own team; approves/rejects vacation requests; sees org tree below them |
| **DOTTED_LINE_MANAGER** | Matrix / project manager | Same team views as solid-line manager |
| **DEPARTMENT_HEAD** | Head of a department | Views all employees in their department; directory access |
| **LOCATION_HEAD** | Office / site lead | Views employees at their location |
| **HIRING_MANAGER** | Recruiter / hiring lead | Directory access for headcount context |
| **EMPLOYEE** | All portal users | Views own profile; self-maintains skills and certifications; submits vacation requests |

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

