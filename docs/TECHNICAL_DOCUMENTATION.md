# HR Portal — Technical Documentation

---

## 1. System Overview

The HR Portal is a multi-tenant, role-based human resources management application built with:

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 · Flask 3.x |
| Database | PostgreSQL 14+ with `uuid-ossp` extension |
| DB Driver | psycopg2 with `RealDictCursor` |
| Frontend | Server-rendered Jinja2 · Vanilla JS · CSS custom properties |
| Static Assets | Single `style.css` · No build step required |
| Auth | Server-side session (Flask `session`, 8-hour TTL) |

---

## 2. Project Structure

```
employeemanagement/
├── app.py                          # All routes, helpers, DB logic
├── static/
│   ├── style.css                   # Full design system + dark mode
│   └── uploads/
│       └── logos/                  # Company logo file uploads (UUID-named)
└── templates/
    ├── base.html                   # Shell: sidebar, topbar, branding injection
    ├── login.html                  # Login + demo user panel
    ├── dashboard.html              # Role-aware stat cards
    ├── directory.html              # Employee directory with filters & pagination
    ├── profile.html                # Employee profile + self-service modals
    ├── admin.html                  # Admin user management panel
    ├── admin_register.html         # 6-step new employee registration
    ├── my_team.html                # Manager team card view
    ├── org_tree.html               # Recursive org hierarchy tree
    ├── company.html                # Company overview page
    ├── admin_companies.html        # Company list (SYSTEM_ADMIN)
    ├── admin_company_form.html     # Company create/edit with branding
    ├── vacation.html               # Employee vacation page
    ├── vacation_team.html          # Manager vacation approval/schedule
    ├── admin_vacation_types.html   # Vacation type list (SYSTEM_ADMIN)
    └── admin_vacation_type_form.html # Vacation type create/edit with rules
```

---

## 3. Database Schema

### 3.1 Core Tables

#### `companies`
Represents a legal entity. All employees, vacation types, and branding belong to one company.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Auto-generated |
| `name` | VARCHAR(200) | Unique company name |
| `industry` | VARCHAR(100) | Optional |
| `website` | VARCHAR(255) | Optional |
| `logo_url` | TEXT | Uploaded path `/static/uploads/logos/…` or external URL |
| `theme_color` | VARCHAR(7) | Hex colour, default `#2563eb` |
| `header_html` | TEXT | Raw HTML injected above all pages for company employees |
| `footer_html` | TEXT | Raw HTML injected below all pages |
| `hq_address` | TEXT | Optional |
| `founded_year` | INTEGER | Optional |
| `description` | TEXT | Optional |
| `is_active` | BOOLEAN | Inactive companies cannot receive new employees |

#### `employees`
Core person record. One employee belongs to one company.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `employee_number` | VARCHAR(50) UNIQUE | Auto-generated EMP-001 … EMP-NNN |
| `first_name`, `last_name` | VARCHAR(100) | |
| `email` | VARCHAR(255) UNIQUE | |
| `employment_status` | VARCHAR(50) | `ACTIVE` / `INACTIVE` / `RESIGNED` / `TERMINATED` |
| `employment_type` | VARCHAR(50) | `PERMANENT` / `CONTRACTOR` / `INTERN` / `PART_TIME` |
| `join_date` | DATE | Used for tenure calculations and anniversary badges |
| `gender` | VARCHAR(10) | `MALE` / `FEMALE` / `OTHER`; drives vacation eligibility |
| `company_id` | UUID FK → `companies` | |

#### `users`
Portal login account; 1-to-1 with employee.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `employee_id` | UUID FK UNIQUE | |
| `email` | VARCHAR(255) UNIQUE | Used as login credential |
| `is_active` | BOOLEAN | Admins can disable login |
| `last_login_at` | TIMESTAMP | Updated on every login |
| `theme_preference` | VARCHAR(10) | `light` / `dark`; persisted per user |

#### `roles` + `user_roles`
- `roles`: static lookup — 8 predefined roles
- `user_roles`: many-to-many join `user_id` → `role_id`

### 3.2 Org Structure Tables

```
companies
  └── business_units          (company_id FK)
        └── functional_units  (business_unit_id FK)
  └── locations               (company_id FK)
  └── cost_centers            (company_id FK)

employee_org_assignments
  employee_id, location_id, business_unit_id,
  functional_unit_id, cost_center_id
  is_current BOOLEAN  ← only one current assignment per employee
```

#### `manager_relationships`

| Column | Type | Notes |
|--------|------|-------|
| `employee_id` | UUID FK | The subordinate |
| `manager_id` | UUID FK | The manager |
| `relationship_type` | VARCHAR | `SOLID_LINE` / `DOTTED_LINE` |
| `is_current` | BOOLEAN | Only current records used in queries |

Constraint: `employee_id <> manager_id` (no self-reporting).

### 3.3 Skills Tables

```
skill_categories → skills → employee_skills
                              ├── self_rating_level_id FK → proficiency_levels
                              ├── manager_validated_level_id FK → proficiency_levels
                              ├── validation_status: SELF_ASSESSED | PENDING_MANAGER_VALIDATION | VALIDATED | REJECTED
                              └── years_of_experience NUMERIC(4,1)
```

`proficiency_levels` stores named levels (🌱 Beginner, 💡 Intermediate, ⚡ Advanced, 🏆 Expert) with numeric ordering.

### 3.4 Vacation Tables

```
vacation_types (company_id FK)
  ├── vacation_type_locations  ← zero rows = company-wide; rows = location-scoped
  └── vacation_type_rules      ← eligibility rules (AND logic)
        rule_type: GENDER_EQ | MIN_TENURE_MONTHS | MIN_TENURE_YEARS
        rule_value: TEXT (compared against employee computed fields)

vacation_requests
  employee_id, vacation_type_id, manager_id,
  start_date, end_date, working_days,
  status: PENDING | APPROVED | REJECTED | CANCELLED
  manager_note TEXT
```

---

### 3.5 Position Change (Org-Change) Tables

Migration: `database/migrations/06_org_change_workflow.sql`. Powers the drag-and-drop position-change feature (see §19).

```
org_change_workflows          ← one active chain per company (company_id UNIQUE)
  └── org_change_workflow_steps  ← ordered approval levels
        step_order INT
        approver_type: ROLE | EMPLOYEE
        approver_role  (role NAME — roles are per-company) | approver_employee_id
        CHECK: exactly one of role / employee set per type

org_change_requests             ← a proposed move
  company_id, employee_id (subject), requested_by_user_id, reason
  from_business_unit_id / from_functional_unit_id / from_location_id / from_manager_id   (audit snapshot)
  proposed_business_unit_id / proposed_functional_unit_id / proposed_location_id / proposed_manager_id
  workflow_id, current_step INT,
  status: PENDING | APPROVED | REJECTED | CANCELLED

org_change_approvals            ← one row per step (audit trail)
  request_id, step_order, approver_type, approver_role, approver_employee_id,
  decided_by_user_id, decision: APPROVED | REJECTED, note, decided_at
```

Feature gate: a new `org_change` row in `portal_features`, with default `role_feature_access` (read+write) for `SOLID_LINE_MANAGER`, `HR_ADMIN`, `PORTAL_ADMIN` (also seeded in `scripts/setup_db.py`).

### 3.6 Audit Table

Migration: `database/migrations/08_audit_log.sql` (reverse with `08_audit_log_down.sql`). One
append-only, company-scoped trail shared by every subsystem — see **§23** for the service and the rules.

#### `audit_log`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGSERIAL PK | **Deliberately not UUID.** Append + range-scan-by-time only; a monotonic key keeps inserts at the B-tree right edge (ADR-009 §3.1) |
| `company_id` | UUID NOT NULL → `companies(id)` | Tenant scope. Taken from the **affected entity**, never the session. No `ON DELETE` — the trail is not removable by deleting the company |
| `actor_user_id` | UUID NULL → `users(id)` ON DELETE SET NULL | |
| `actor_employee_id` | UUID NULL → `employees(id)` ON DELETE SET NULL | |
| `actor_label` | VARCHAR(255) NOT NULL | `"Name <email>"` **as at the time of the action** — denormalised so a later delete cannot anonymise the history |
| `actor_roles` | JSONB NOT NULL `[]` | Snapshot of the roles the actor held at the time |
| `actor_ip` / `actor_session_id` | VARCHAR NULL | Best-effort; only fully meaningful once real auth lands (EP28) |
| `subject_employee_id` | UUID NULL → `employees(id)` ON DELETE SET NULL | |
| `subject_employee_number` | VARCHAR(50) NULL | **The subject's name is never stored** — an audit row must survive a GDPR erasure without re-leaking the erased data |
| `action` | VARCHAR(60) NOT NULL | Closed enumeration held in `audit_service.ACTIONS`, not a DB CHECK, so later epics extend it without a migration |
| `entity_type` / `entity_id` | VARCHAR(50) / UUID NOT NULL | Polymorphic — no FK on `entity_id` |
| `before_state` / `after_state` | JSONB NULL | **Field-level diffs only, never whole rows.** Both sides must carry the same key set |
| `reason` | TEXT NOT NULL | `CHECK (btrim(reason) <> '')` — every row answers "why" |
| `correlation_id` | UUID NOT NULL | Groups every row from one unit of work, so an offboarding reads as one story |
| `outcome` / `error_code` | VARCHAR NOT NULL `'SUCCESS'` / VARCHAR NULL | `CHECK (outcome IN ('SUCCESS','FAILED'))` |
| `metadata` | JSONB NOT NULL `{}` | Same PII rules as the diff |
| `retention_class` | VARCHAR(20) NOT NULL `'STANDARD'` | `STANDARD` / `EMPLOYMENT` / `SECURITY`. Written now so a future purge job needs no backfill; the retention **periods** are a legal determination and nothing is purged until they exist |
| `created_at` | **TIMESTAMPTZ** NOT NULL `NOW()` | The only timezone-aware timestamp in the schema. Deliberate — "when" must be unambiguous here (TD-12) |

Indexes: `idx_audit_entity (company_id, entity_type, entity_id, created_at DESC)`,
`idx_audit_company_time (company_id, created_at DESC)`, `idx_audit_correlation (company_id, correlation_id)`.
No GIN index on the JSONB columns — nothing queries inside the blobs yet.

**Append-only is enforced in the database:** `audit_log_immutable()` + trigger `trg_audit_log_no_update`
(BEFORE UPDATE) raises `audit_log is append-only (attempted UPDATE)`. **`DELETE` is deliberately NOT
blocked** — retention purge must be able to delete and there is no DB role separation here to tell a purge
job from the app user; blocking it would either make retention impossible or force an escape hatch any code
path could set. Tracked as **TD-13**, with the purge role belonging to the purge job's own story.

Feature gate: an `audit_log` row in `portal_features` (`sort_order` 13 — 11/12 are reserved for
`onboarding`/`offboarding`), with default `role_feature_access` **read-only** for `PORTAL_ADMIN` and
`HR_ADMIN` (also seeded in `scripts/setup_db.py`). Never granted to `EMPLOYEE`.

---

## 4. Application Architecture

### 4.1 Request Lifecycle

```
Browser → Flask Route
            │
            ├─ @login_required / @require_roles decorator
            │     └─ checks session['user_id'] and session['roles']
            │
            ├─ get_db() → psycopg2 connection (stored in Flask g, autocommit=True)
            │
            ├─ query() / execute() / insert_returning()
            │     └─ composite writes wrapped in with transaction():
            │            one commit, one rollback (ADR-006)
            │
            └─ render_template() or jsonify()
                  │
                  inject_ctx() context processor injects:
                    has_role(), session, request, now,
                    branding{}, theme_pref
```

### 4.2 Key Helper Functions

| Function | Purpose |
|----------|---------|
| `query(sql, params, one)` | SELECT; returns list of dicts or single dict. Runs under autocommit, so a read never leaves the connection idle-in-transaction |
| `execute(sql, params)` | INSERT/UPDATE/DELETE. Stands alone (autocommit) **unless** a `transaction()` block is open, in which case the block commits |
| `insert_returning(sql, params)` | INSERT … RETURNING id; returns first row as dict. Same commit rule as `execute()` |
| `transaction()` | Context manager making a composite write **one unit of work** — single commit, single rollback (see §4.2a) |
| `to_dict(row)` | Converts RealDictRow; serialises datetime → ISO, Decimal → float |
| `_next_employee_number()` | Computes next EMP-NNN from current MAX |
| `_vacation_types_for_employee(emp_id)` | Location filter + rule evaluation |
| `_employee_solid_manager(emp_id)` | Returns solid-line manager UUID |
| `_used_days(emp_id, vt_id, year)` | Sums PENDING+APPROVED working days for year |
| `_save_logo(file_storage, old_url)` | Saves uploaded logo, cleans up old file |
| `_build_nested(flat)` | Converts flat CTE rows → nested tree dict |

### 4.2a Transactions — `transaction()` (ADR-006 / KAN-155)

Connections are opened with `autocommit = True`. A single statement is therefore durable on its own,
reads never hold an open transaction, and a failed statement cannot poison the rest of the request
with `current transaction is aborted`.

**Anything that writes more than one row/table must opt in to a transaction:**

```python
from app.db import transaction, execute, insert_returning

with transaction():
    vt = insert_returning("INSERT INTO vacation_types (...) VALUES (...) RETURNING id::text", (...))
    for lid in location_ids:
        execute("INSERT INTO vacation_type_locations VALUES (%s::uuid,%s::uuid)", (vt['id'], lid))
```

Inside the block `execute()` / `insert_returning()` **do not commit individually** — that is the whole
point. A failure anywhere in the block rolls back every earlier statement in it, so a partly-written
composite can never become durable. On exit the block commits exactly once and autocommit is restored.

Rules:

| Rule | Why |
|---|---|
| One `transaction()` per public entry point — not per cascade, not per table | The unit of work is the business operation, not the statement |
| Side effects that cannot be undone (notifications, email) go **after** the block | A committed notification for a rolled-back change is unrecoverable |
| Never nest — a helper runs inside the caller's open block | A nested block would commit independently and create a false boundary. Nesting raises `RuntimeError` |

**Wrapped today:** vacation-type create and edit (`app/routes/vacation.py`); org-change
`save_workflow`, `create_request`, `apply_change`, and each `decide()` outcome — including final
approval, where the step decision, the applied move and the request close-out commit together
(`app/services/org_change_service.py`). `apply_change()` is the atomic standalone entry point;
`decide()` calls the inner `_apply_change()` inside its own wider transaction.

**Not yet wrapped** (found during KAN-155, tracked separately — deliberately out of its scope):
employee registration (`app/routes/admin.py` `admin_register_user`), role reassignment
(`api_update_roles` — delete-all then re-insert), company-role seeding and per-company admin
seeding (`seed_company_roles`, `api_seed_company_admin_user`, `api_company_role_set_permissions`),
company create with its seeded admin (`app/routes/company.py`), and CSV import apply
(`app/services/import_service.py`, a per-row loop). See the Architect's debt register.

### 4.3 Session Keys

| Key | Type | Set by |
|-----|------|--------|
| `user_id` | str (UUID) | login |
| `employee_id` | str (UUID) | login |
| `user_name` | str | login |
| `user_email` | str | login |
| `user_title` | str | login |
| `roles` | list[str] | login |
| `theme_pref` | `'light'` or `'dark'` | login; updated by `/api/user/theme` |
| `branding` | dict | login; updated by `admin_company_edit` |

`branding` dict keys: `theme_color`, `header_html`, `footer_html`, `logo_url`, `company_name`

---

## 5. API Reference

### Authentication APIs
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET/POST | `/login` | — | Login form |
| GET | `/logout` | any | Clear session |
| POST | `/api/user/theme` | login | Save `light`/`dark` preference |

### Profile APIs (own profile only)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/profile/gender` | Save gender |
| POST | `/api/profile/skills` | Add or update a skill + self-rating |
| DELETE | `/api/profile/skills/<id>` | Remove a skill |
| POST | `/api/profile/certifications` | Add certification |
| PUT | `/api/profile/certifications/<id>` | Update certification |
| DELETE | `/api/profile/certifications/<id>` | Remove certification |

### Admin APIs
| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/admin/users` | SYSTEM_ADMIN | All users with roles |
| POST | `/api/admin/update-roles` | SYSTEM_ADMIN | Replace user role set |
| POST | `/api/admin/toggle-user` | SYSTEM_ADMIN | Enable/disable user |
| POST | `/api/admin/validate-skill` | SYSTEM_ADMIN, HR_ADMIN | Validate employee skill |
| GET | `/api/admin/org/business-units` | SYSTEM_ADMIN, HR_ADMIN | BUs with FU children |
| GET | `/api/admin/org/locations` | SYSTEM_ADMIN, HR_ADMIN | Locations |
| GET | `/api/admin/org/functional-units` | SYSTEM_ADMIN, HR_ADMIN | FUs filtered by BU |
| GET | `/api/admin/refresh-settings` | SYSTEM_ADMIN | Get per-role refresh intervals |
| POST | `/api/admin/refresh-settings` | SYSTEM_ADMIN | Set per-role refresh intervals |
| GET | `/api/admin/vacation-rules` | SYSTEM_ADMIN | Rules for vacation type IDs |

### Org & Directory APIs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/employees` | Paginated employee list with filters |
| GET | `/api/my-team` | Direct reports of logged-in manager |
| GET | `/api/org-tree?root=<id>` | Recursive tree from root (defaults to session employee) |
| GET | `/api/org-tree/context?of=<id>` | Focus employee info + full ancestor chain for nav breadcrumb |
| GET | `/api/dashboard/stats` | Role-filtered dashboard metrics |

### Vacation APIs
| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/api/vacation/request` | any | Submit vacation request |
| DELETE | `/api/vacation/request/<id>` | any | Cancel own PENDING request |
| GET | `/api/vacation/team-pending` | manager+ | Pending requests for my reportees |
| GET | `/api/vacation/team-upcoming` | manager+ | Upcoming approved/pending leave |
| GET | `/api/vacation/team-pending-counts` | manager+ | Per-employee pending counts |
| POST | `/api/vacation/review/<id>` | manager+ | Approve or reject a request |

Vacation submit/review responses and the manager pending list (`team-pending`) now include per-type balance fields (`max_days`, `used_days`) so the UI can render remaining balance in the request modal, type cards, pending list, and review modal.

### Position Change (Org-Change) APIs
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| GET | `/org-change` | `org_change` (r) | Position Changes inbox page (Pending My Approval + My Requests) |
| POST | `/api/org-change/request` | `org_change` (w) + must manage subject, or be HR/Portal | **The single creation path** for both drag-and-drop and Transfer… (§22.5a). Validates initiator (`EMPLOYEE` cannot self-initiate), ACTIVE subject + manager, company scope of every proposed unit, reporting cycles, no-op moves, and one PENDING request per person (`409`) |
| GET | `/api/org-change/pending` | `org_change` (r) | Requests whose **current** step this user may decide |
| GET | `/api/org-change/my-requests` | login | Requests the caller raised (status + level) |
| GET | `/api/org-change/pending-count` | login | Count for the bell/badge |
| POST | `/api/org-change/<id>/decide` | `org_change` (w) | Approve/reject the current step (advances or stops the chain) |
| POST | `/api/org-change/<id>/cancel` | login (requester or admin) | Cancel a PENDING request |
| GET | `/api/org-change/prefill?target=&subject=` | `org_change` (w) | Everything the dialog needs, for both entry points: drop-target placement, company BU/FU/location/manager option lists, and (when `subject` is given) the subject, their current placement **by name**, the company's approval chain, their direct-report count and any PENDING request id |
| GET/POST | `/admin/org-change-workflow`, `/api/admin/org-change-workflow` | `org_structure` (w) | Config page + load / replace-all workflow steps |

---

## 6. Vacation Eligibility Engine

`_vacation_types_for_employee(emp_id)` runs in two stages:

**Stage 1 — SQL location filter:**
```sql
WHERE vt.is_active AND vt.company_id = <company>
AND (
    COALESCE(location_count, 0) = 0         -- company-wide type
    OR EXISTS (
        SELECT 1 FROM vacation_type_locations vtl
        JOIN employee_org_assignments oa ON oa.location_id = vtl.location_id
        WHERE vtl.vacation_type_id = vt.id AND oa.employee_id = <emp> AND oa.is_current
    )
)
```

**Stage 2 — Python rule evaluation (AND logic):**
```python
for rule in rules_for_type:
    if rule_type == 'GENDER_EQ':
        pass &= (employee.gender.upper() == rule_value.upper())
    elif rule_type == 'MIN_TENURE_MONTHS':
        pass &= (tenure_months >= float(rule_value))
    elif rule_type == 'MIN_TENURE_YEARS':
        pass &= (tenure_years >= float(rule_value))
```
Tenure is computed as `(today - join_date).days / 30.44` (months) and `/ 365.25` (years).

---

## 7. Org Tree — Family Tree Layout

### Visual design
The org chart renders as a **top-down family tree** (not a folder/indent list). Each person is a card node; children fan out horizontally below their parent connected by CSS T-connector lines:

```
              ┌──────────┐
              │  CEO     │
              └────┬─────┘
       ┌───────────┼───────────┐
 ┌─────┴─────┐ ┌───┴────┐ ┌───┴────┐
 │ VP Eng    │ │ VP Fin │ │ VP HR  │
 └─────┬─────┘ └────────┘ └────────┘
    ┌──┴──┐
 ┌──┴──┐ ┌┴────┐
 │ Mgr │ │ Mgr │
 └─────┘ └─────┘
```

Each card shows: avatar (initials, colour-coded), full name, job title, location.  
Cards link to the employee's full profile. A **Focus ↓** button (visible on hover) zooms the tree into that person's subtree.

### Navigation

The tree is **employee-centric**: it always starts from the currently logged-in employee. Two navigation mechanisms allow movement:

| Control | Action |
|---------|--------|
| **↑ [Manager Name]** button | Navigate up — loads the manager's subtree as the new root |
| **Breadcrumb** (ancestor chain) | Click any ancestor to jump directly to their subtree |
| **Focus ↓** on a card | Navigate down — loads that person's subtree as the new root |
| **← My view** button | Returns to the logged-in employee's own subtree |

Access: `@login_required` — all employees can view; the tree always starts at their own node.

### Downward tree CTE (`TREE_CTE` in `helpers.py`)

PostgreSQL recursive CTE, depth-limited to 10 levels:

```sql
WITH RECURSIVE tree AS (
    -- Base case: the focus employee
    SELECT e.id, ..., NULL::uuid AS manager_id, 0 AS depth
    FROM employees e WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE'

    UNION ALL

    -- Recursive: employees whose SOLID_LINE manager is already in the tree
    SELECT e.id, ..., mr.manager_id, t.depth + 1
    FROM employees e
    JOIN manager_relationships mr ON mr.employee_id = e.id
        AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
    JOIN tree t ON t.id = mr.manager_id
    WHERE e.employment_status='ACTIVE' AND t.depth < 10
)
```

`build_nested(flat)` converts the ordered flat list into `{..., children: [...]}` consumed by `buildNode()`.

### Upward ancestor CTE (`/api/org-tree/context`)

A second recursive CTE walks **upwards** from the focus employee to build the breadcrumb:

```sql
WITH RECURSIVE up AS (
    SELECT mr.manager_id AS id, 1 AS level
    FROM manager_relationships mr
    WHERE mr.employee_id = %s::uuid
      AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
    UNION ALL
    SELECT mr.manager_id, up.level + 1
    FROM manager_relationships mr
    JOIN up ON mr.employee_id = up.id
    WHERE mr.relationship_type = 'SOLID_LINE' AND mr.is_current
)
SELECT e.id::text, e.first_name, e.last_name, e.job_title
FROM up JOIN employees e ON e.id = up.id
ORDER BY up.level DESC  -- CEO first, direct manager last
```

Returns `{ focus: {...}, ancestors: [{...}, ...] }`.

### CSS connector pattern

The T-connector lines between parent and children are drawn entirely with CSS pseudo-elements — no SVG:

```css
/* Horizontal connector spanning all siblings */
.ft-row > .ft-node::before  { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.ft-row > .ft-node:first-child::before { left: 50%; }   /* trim left  */
.ft-row > .ft-node:last-child::before  { right: 50%; }  /* trim right */
.ft-row > .ft-node:only-child::before  { display: none; }

/* Vertical drop from connector to card */
.ft-row > .ft-node::after   { content:''; top:0; left:50%; width:2px; height:22px; }
```

The vertical stem from parent card to the horizontal connector is a `<div class="ft-stem">` (2×22 px).

---

## 8. Branding & Theming System

### Company Branding Flow
1. Admin saves company → `theme_color`, `header_html`, `footer_html`, `logo_url` stored in DB
2. `admin_company_edit` POST re-fetches and updates `session['branding']` immediately
3. `inject_ctx()` context processor exposes `branding` to every template
4. `base.html` applies at render time:
   - `<html data-theme="{{ theme_pref }}">` — dark mode class
   - Inline `<style>:root { --primary: {{ branding.theme_color }} }</style>` — colour override
   - `{{ branding.header_html | safe }}` — company header
   - `{{ branding.footer_html | safe }}` — company footer
   - `<img src="{{ branding.logo_url }}">` — sidebar logo

### Dark Mode CSS Architecture
All colours are CSS custom properties on `:root`. Dark mode overrides via attribute selector:
```css
[data-theme="dark"] {
  --bg: #0f172a;  --card: #1e293b;  --border: #334155;
  --text: #e2e8f0;  --muted: #94a3b8;
  --topbar-bg: #1e293b;  --input-bg: #0f172a; …
}
```
Toggle calls `POST /api/user/theme` → updates `users.theme_preference` → updates `session['theme_pref']` → applied on next page render (or immediately via `document.documentElement.setAttribute('data-theme', next)`).

### Logo Upload Storage
- Files saved to `static/uploads/logos/<uuid>.<ext>`
- Served by Flask's built-in static file handler at `/static/uploads/logos/…`
- On replacement: old local file is `os.remove()`d if its path starts with `/static/uploads/logos/`
- Allowed formats: `png`, `jpg`, `jpeg`, `gif`, `svg`, `webp`
- Client-side validation: type check + 2 MB size limit before submit

---

## 8b. Shell Accessibility Primitives (KAN-204 · tagged **EP33**)

Three primitives the whole product shares. **A new screen's accessibility should be a call to
one of these, not a tenth private reimplementation** — that duplication is what D-004 exists to
prevent, and EP42 alone adds about ten surfaces.

Tagged **EP33** because this is EP33's debt: EP38 was believed to have delivered it and had not
(UX verified three of nine shell fixes). Delivered in W0 so the EP42 screens have something to
call. `TestShellFocusVisibility`, `TestShellLiveRegions` and `TestShellReducedMotion` in
`tests/test_ui_ux.py` fail if any of it is removed or reimplemented locally.

### 1. Focus visibility — `:focus-visible` (WCAG 2.4.7)

One token, one rule, in `static/css/style.css`:

```css
:root                { --focus-ring: #2563eb; }   /* light */
[data-theme="dark"]  { --focus-ring: #60a5fa; }   /* lighter — 3:1 on #0f172a */

:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }
```

**The rule is deliberately the last thing in the stylesheet, and that is load-bearing.**
`:focus-visible` carries one class-worth of specificity (0,1,0) — identical to `.search-input`,
`select.filter-sel` and `.rows-select`, each of which sets `outline: none`. It beats them by
**source order alone**. Move it up the file and those three controls silently lose their focus
ring again. A test asserts the ordering, and asserts no new `outline: none` appears after it.

- `:focus-visible`, not `:focus` — a mouse click must not leave a ring behind.
- Two per-component rings (`.row-menu-btn`, `.row-menu-list > *`) are 0,2,0 and still win. They
  are tuned to sit inside a tight menu; leave them.
- Don't add a screen-local focus style. If a control needs different treatment, adjust the
  offset, not the colour.

### 2. Shared ARIA live regions — the only two in the product

Declared once, first in `<body>` in `templates/base.html`:

```html
<span id="live-status" class="sr-only" role="status" aria-live="polite"></span>
<span id="live-alert"  class="sr-only" role="alert"  aria-live="assertive"></span>
```

- **First in `<body>` on purpose.** A live region injected at the same moment as its text is not
  reliably announced — there was no prior state for the change to be measured against.
- **`.sr-only`, never `display:none` or `hidden`.** Those remove the element from the
  accessibility tree, which silences it. It looks like it works and announces nothing.
- **Two, not one**, because the difference is behavioural, not cosmetic: `polite` waits for a
  pause in current speech; `assertive` interrupts.
- **No screen may declare its own.** A grep-assert over `templates/` fails the build if a second
  pair appears. The move dialog owned the product's first pair and was migrated here; that file
  is included on three pages, so a private pair would have meant competing copies.

### 3. `announce(msg, level)` — the way to reach them

Defined once in `templates/base.html`. Call it wherever something changes visibly but silently:

```js
announce('Position change submitted for approval.');            // polite (default)
announce('Pick at least one change.', 'assertive');             // interrupts
```

| Rule | Why |
|---|---|
| Default is `polite` | An announcement that cuts a screen-reader user off mid-sentence to say "loaded" is worse than silence. Reserve `assertive` for errors and data loss. |
| Never throws | A missing region returns early. An announcement must not break the flow that was announcing. |
| Re-announces a repeat | A screen reader only speaks a *change*, so re-sending identical text would be silent — which is wrong for the same validation error twice, exactly when the user needs to hear it again. That path clears and re-sets on a later tick; a new message is set synchronously and is observable to a test immediately. |

**Announce these:** a save, an error, a filter that changed the row count, an empty state, an
approval step advancing. Current callers: the shared move dialog (status + errors) and the
directory (result count and empty state, guarded on a *changed* count so paging stays quiet).

### 4. Reduced motion — `prefers-reduced-motion` (WCAG 2.3.3)

A universal block at the foot of the stylesheet, covering all ~57 transitions and every keyframe
animation at once, so no screen has to remember:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- **`.01ms`, not `0s`.** A zero duration fires no `transitionend` / `animationend`, so any code
  waiting on one would hang for ever.
- It matters most for the three **infinite** animations — `pulse`, `anniv-sway`,
  `anniv-pulse-scale`. A permanently throbbing badge is the exact trigger this query exists for.
- **Motion only.** Colour, outline and tint cues are untouched, including the org tree's
  drag-and-drop dashed outline — nothing communicated by movement alone is lost.

---

## 9. Security Considerations

| Area | Implementation |
|------|---------------|
| **Route protection** | `@login_required` + `@require_roles(*roles)` / `@require_feature_access(...)` decorators on every non-public route and API |
| **Runtime defaults** | `APP_ENV=production` **fails fast** if `SECRET_KEY` is unset; `SESSION_COOKIE_HTTPONLY` + `SAMESITE=Lax` always, `SECURE` in production; `debug` driven by env (off in prod); `MAX_CONTENT_LENGTH` caps upload/body size (`app/config.py`, KAN-152) |
| **Session integrity** | Flask signed-cookie session; `SECRET_KEY` from env var (see above) |
| **XSS** | Jinja2 auto-escapes template variables; JS builders route dynamic values through the global `escH()` helper on the directory, org-tree, team-vacation and my-team screens (KAN-150; remaining screens tracked under KAN-173). `| safe` still used for admin-controlled `header_html` / `footer_html` — sanitisation tracked under KAN-151 |
| **SQL injection** | All DB calls use parameterised queries via psycopg2; audited clean — dynamic `WHERE` fragments interpolate only fixed internal strings, never user input |
| **File uploads** | Extension allowlist; UUID filename (no user-controlled path); size validated client-side + `MAX_CONTENT_LENGTH` server-side. SVG hardening tracked under KAN-151 |
| **IDOR prevention** | Profile self-edit APIs check `session['employee_id']`; vacation cancel checks `employee_id` ownership; org-change requires the initiator to manage the subject or be HR/Portal admin |
| **CSRF** | Not yet implemented — tracked under **KAN-149** (EP28) |
| **Authentication** | Email-only login (demo). Real auth factor tracked under **KAN-148** (EP28) before any production use |

> Full audit and remaining hardening backlog: `docs/ARCHITECTURE_REVIEW.md` (EP28).

---

## 10. Deployment Notes

### Environment Variables
```bash
APP_ENV=production            # 'development' (default) | 'production'
SECRET_KEY=<random-256-bit-string>   # REQUIRED when APP_ENV=production (app fails fast if unset)
FLASK_DEBUG=0                 # optional override; defaults on in dev, off in production
MAX_CONTENT_LENGTH=8388608    # optional; default 8 MB request/upload cap
PGHOST=localhost
PGPORT=5432
PGDATABASE=employee
PGUSER=<db-user>
PGPASSWORD=<db-password>
```

In production, `APP_ENV=production` also turns on `SESSION_COOKIE_SECURE` and forces `debug=False`
(`app/config.py`). Serve strictly over HTTPS behind a proxy so the Secure cookie is honoured.

### Building the database
`database/schema.sql` is the **authoritative** schema (a `pg_dump --schema-only` baseline of all 47
tables/indexes/functions/triggers). Build a fresh DB from it, then seed:
```bash
psql -d employee -f database/schema.sql        # full structure (canonical)
psql -d employee -f database/seed_rbac.sql      # companies + roles + portal_features + role_feature_access
python scripts/setup_db.py                       # demo data (Telia seed) — see caveat below
```
> `database/schema_v2.sql` and `database/migrations/*.sql` are **historical** — a fresh DB uses
> `schema.sql`, not migration replay. Add new schema changes as a numbered migration **and** regenerate
> `schema.sql`. Note: `setup_db.py` currently targets the old schema and is not idempotent against
> `schema.sql` (tracked under KAN-167); `seed_rbac.sql` provides the RBAC seed CI and tests rely on.

### Running the Server
```bash
python run.py                               # dev mode, port 8000, debug from env
APP_ENV=production SECRET_KEY=… gunicorn -w 4 -b 0.0.0.0:8000 "app:app"   # production
```

### Required PostgreSQL Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Uploads Directory
The `static/uploads/logos/` directory must be writable by the application process. It is committed with a `.gitkeep`. In production, point to a persistent volume or S3-backed mount.

---

## 11. Testing

### Overview
The test suite uses **pytest** and **pytest-flask** (~4,500 tests). Most tests mock the DB with
`unittest.mock`, but ~800 render full pages that fire incidental unmocked queries (feature-access, nav)
and therefore need a **live schema + RBAC seed** — locally satisfied by the running dev DB.

```bash
python -m pytest -q                    # run all tests (needs the seeded dev DB up)
python -m pytest tests/test_helpers.py # single file
```

### Continuous Integration — `.github/workflows/ci.yml`
Runs on every push to `main` and every PR (KAN-169):
- **Test suite** — spins up Postgres, builds from `database/schema.sql` + `database/seed_rbac.sql`, runs
  `pytest --ignore=tests/ui`.
- **Fresh-DB schema + app boot** — builds from `schema.sql` alone (no seed), asserts core + `org_change`
  tables exist, and boots the app (`GET /login` runs real queries). This catches schema drift the mocked
  suite cannot — e.g. a feature enabled in nav whose backing tables are missing from `schema.sql`.

### Browser regression suites (`tests/ui/`) — standalone, NOT part of pytest/CI
Headless Playwright scripts run directly against a live server on `http://localhost:8000`:
```bash
python tests/ui/test_browser.py            # 77 checks: login, admin, org tree, search, vacation, directory,
                                           #  Portal-Admin scoping, restricted access, mobile, redirects
python tests/ui/test_vacation_workflow.py  # 39 checks: full submit → approve → reject → history workflow
```
Per `CLAUDE.md`, run these before confirming any substantial change. (A **"flow test"** the user asks for
is a separate, VISIBLE Chrome + audio session — see the FLOW TESTS rule in `CLAUDE.md`.)

### Local pre-commit gate
`.git/hooks/pre-commit` runs the full `pytest` suite and aborts the commit on failure (requires the dev DB up).

### Test Structure

```
tests/
├── conftest.py                    # Fixtures: app, client, session helpers, sample data
├── test_db.py                     # serialize() and to_dict() helpers
├── test_transactions.py           # transaction() — atomicity, rollback, nesting (real DB tier auto-skips)
├── test_helpers.py                # Business logic and pure functions
├── test_auth.py                   # Auth decorators and login/logout routes
├── test_routes_employees.py       # Employee directory, profile, self-edit APIs
├── test_routes_vacation.py        # Vacation submit, cancel, review workflow
├── test_routes_admin.py           # Admin panel, user/role management, company admin
├── test_routes_auth_login.py      # Login/logout flows, session keys, access control
├── test_routes_org.py             # Org CRUD, company scoping, context switcher, permissions matrix
└── test_ui_ux.py                  # UI/UX regression: template structure, CSS paths, asset integrity
```

### Test Coverage Summary

| File | Tests | What is covered |
|------|-------|----------------|
| `test_db.py` | 13 | `serialize()` — date, datetime, Decimal, primitives; `to_dict()` — type conversion |
| `test_transactions.py` | 12 | `transaction()` (KAN-155): statements not durable until the single commit, mid-write failure retracts everything, autocommit restored after commit *and* rollback, nesting refused, reads never idle-in-transaction. Includes a **real-Postgres tier** (skipped when no DB is reachable) proving a failed vacation-type composite write leaves no rows |
| `test_helpers.py` | 39 | `rule_label`, `build_nested`, `next_employee_number`, `employee_solid_manager`, `used_days`, `is_direct_report`, vacation eligibility engine, `save_logo` |
| `test_auth.py` | 18 | `@login_required`, `@require_roles`, login form, unknown email error, logout |
| `test_routes_employees.py` | 24 | Directory role gating, profile, self-edit APIs |
| `test_routes_vacation.py` | 20 | Vacation submit, cancel, review (all edge cases) |
| `test_routes_admin.py` | 19 | Admin panel, register user, user list, roles, toggle, validate skill, companies |
| `test_routes_auth_login.py` | 21 | POST login sets session keys, company_id stored, Tech Admin gets null company, branding loaded, protected-route redirects |
| `test_routes_org.py` | 31 | BU/loc/FU list with company filter, create (conflict, missing name), update (403 cross-company), delete (409 with employees), company context switch, role-feature permission matrix CRUD |
| `test_ui_ux.py` | 48 | Login page 200/CSS path/split-panel structure/demo chips/no-old-classes, base.html CSS path, sidebar nav gating, admin panel tab visibility, CSS file integrity (all classes defined), template asset consistency (no bare `style.css`) |
| `test_org_change.py` | 18 | Position-change initiator permissions (employee blocked, manager own-reports-only, HR/Portal open), sequential `decide` (advance / reject-stops / final-applies), approver eligibility, `apply_change` SQL, `create_request` notifications, workflow-config save, **and the KAN-155 transaction boundaries** — every write inside exactly one committed unit, notifications only after commit, a failed final approval commits nothing and notifies nobody |
| `test_audit_service.py` | 44 | Audit subsystem (KAN-187 / ADR-009): the twelve required audit fields, closed action enumeration, mandatory `company_id` and `reason`, diff-only/no-nesting/no-secrets rules, subject never named. **Transaction mechanics** — `record()` commits nothing inside the caller's block and opens no transaction of its own; a rolled-back change leaves no audit row. **Real-Postgres tier** — atomic commit with the audited change, append-only trigger rejects targeted *and* blanket `UPDATE`, `company_id` NOT NULL, cross-tenant isolation, and the migration applies/re-applies/reverses on a fresh database |
| **Total (representative core files)** | **312** | Full repository suite: **4,568 passing** |

### Pre-Commit Test Gate

A Git pre-commit hook at `.git/hooks/pre-commit` runs the full 238-test suite before every commit. If any test fails the commit is aborted. This catches regressions before they reach the repository.

```bash
# The hook runs:
python -m pytest tests/ -q --tb=short
```

### Key Fixtures (conftest.py)

| Fixture | Description |
|---------|-------------|
| `client` | Unauthenticated Flask test client |
| `auth_client` | Client with `EMPLOYEE` session |
| `admin_client` | Client with `SYSTEM_ADMIN` + `EMPLOYEE` session |
| `manager_client` | Client with `SOLID_LINE_MANAGER` + `EMPLOYEE` session |
| `SAMPLE_EMPLOYEE` | Reusable employee dict for mocking `fetch_employees` |
| `SAMPLE_VACATION_TYPE` | Reusable vacation type dict |

### Testing Strategy

- **Pure functions** — called directly, no mocking needed.
- **DB-dependent helpers** — `app.helpers.query` patched at the module-import level.
- **Flask routes** — `app.test_client()` with session pre-seeded; all DB calls in route modules patched individually.
- **Auth enforcement** — 302 redirect for unauthenticated/unauthorised requests, 200 for authorised.
- **Company scoping** — captured SQL parameters inspected to confirm company_id filter is (or is not) applied.
- **UI/UX** — HTML source parsed for CSS class names, asset paths, and structural landmarks; CSS file read directly.

---

## 12. Two-Tier Admin System

### Design

The portal uses two distinct admin tiers to separate platform-level concerns from company-level administration:

| Role | Name | Scope | Company affiliation |
|------|------|-------|-------------------|
| `SYSTEM_ADMIN` | **Tech Admin** | All companies, all data, all settings | None — must have `company_id = NULL` in their employee record |
| `PORTAL_ADMIN` | **Portal Admin** | Their own company only | One specific company |

### Tech Admin (SYSTEM_ADMIN)

- Not affiliated with any company (`employees.company_id = NULL`).
- Sees all users, employees, BUs, locations, FUs, vacation types across every company.
- Can select a **company context** via the switcher in the admin panel header — once selected, all admin sections filter to that company.
- Can assign or revoke any role, including `PORTAL_ADMIN`.
- Can access Widget Settings (global refresh intervals) and the Roles & Permissions matrix.
- The company context is stored in `session['admin_company_id']` (separate from `session['company_id']`).

### Portal Admin (PORTAL_ADMIN)

- Belongs to one specific company (`employees.company_id` is set).
- At login, `session['company_id']` is populated from their employee record.
- All admin queries automatically filter by `session['company_id']` — no cross-company data is ever returned.
- Can manage users, employees, BUs, locations, FUs, vacation types **within their company only**.
- Cannot assign `SYSTEM_ADMIN` or `PORTAL_ADMIN` roles to others (blocked server-side).
- Cannot access Widget Settings or cross-company Companies list.
- Has a **Company Settings** link in the nav to edit their own company's branding.

### `_company_scope()` Helper

All admin route handlers call this function to determine the current company filter:

```python
def _company_scope():
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        return session.get('admin_company_id') or None  # None = all companies
    if 'PORTAL_ADMIN' in roles:
        return session.get('company_id') or None
    return None
```

When the returned value is `None`, queries run without a company filter (Tech Admin, all-companies mode). When a UUID is returned, a `WHERE company_id = %s::uuid` clause is injected.

### DB Migration

```sql
-- Run once: database/migrations/alter_table.sql
ALTER TABLE business_units  ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);
ALTER TABLE locations        ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);
ALTER TABLE functional_units ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);

INSERT INTO roles (name, description)
VALUES ('PORTAL_ADMIN', 'Full administrative access within their assigned company')
ON CONFLICT (name) DO NOTHING;
```

After applying, run `scripts/setup_db.py` to backfill `company_id` on existing rows.

---

## 13. Organisation CRUD (Admin)

Admins can create, update, and delete Business Units, Locations, and Functional Units from the Organisation tab of the Admin Panel.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/org/business-units` | List BUs (company-scoped) |
| POST | `/api/admin/org/business-units` | Create BU |
| PUT | `/api/admin/org/business-units/<id>` | Update BU |
| DELETE | `/api/admin/org/business-units/<id>` | Delete BU (409 if employees assigned) |
| GET | `/api/admin/org/locations` | List locations |
| POST | `/api/admin/org/locations` | Create location |
| PUT | `/api/admin/org/locations/<id>` | Update location |
| DELETE | `/api/admin/org/locations/<id>` | Delete location |
| GET | `/api/admin/org/functional-units` | List FUs |
| POST | `/api/admin/org/functional-units` | Create FU |
| PUT | `/api/admin/org/functional-units/<id>` | Update FU |
| DELETE | `/api/admin/org/functional-units/<id>` | Delete FU |

### Safety Rules

- **DELETE** returns HTTP 409 if any `employee_org_assignments` row has `is_current = TRUE` referencing the record being deleted.
- **PUT/DELETE** for Portal Admin: `_assert_org_ownership()` checks the record's `company_id` matches the session's `company_id`; returns 403 otherwise.
- **POST** for Portal Admin: `company_id` from `_company_scope()` is auto-injected into the INSERT; Portal Admin cannot create records for a different company.

### UI

Each list row in the Organisation tab shows an Edit button (opens pre-filled modal) and a Delete button (disabled with tooltip when employees are assigned). The FU create/edit modal populates the Business Unit dropdown from the currently loaded BU list. All changes save immediately via AJAX and reload the lists.

---

## 14. Feature-Level Permissions Matrix

### Tables

```sql
portal_features (id, code, label, description, sort_order)
role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
```

`portal_features` defines the 11 feature areas:

| code | label | sort_order |
|------|-------|-----------|
| `employee_profiles` | Employee Profiles | 1 |
| `org_structure` | Organisation Structure | 2 |
| `user_accounts` | User Accounts | 3 |
| `skills` | Skills & Certifications | 4 |
| `vacations` | Vacations & Leave | 5 |
| `reports` | Reports & Analytics | 6 |
| `company_settings` | Company Settings | 7 |
| `system_config` | System Configuration | 8 |
| `skills_intelligence` | Skills Intelligence | 9 |
| `org_change` | Position Change Requests | 10 |
| `audit_log` | Audit Log | 13 |

`sort_order` 11 and 12 are reserved for `onboarding` / `offboarding` (EP38 KAN-183/KAN-184).

`role_feature_access` stores three boolean flags (`can_read`, `can_write`, `can_delete`) per role–feature pair.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/roles/features` | Returns `{roles, features, matrix}` — full permission matrix |
| POST | `/api/admin/roles/feature-access` | Update one role–feature cell (upsert) |

Both are restricted to `SYSTEM_ADMIN`. The matrix is rendered in the **Roles & Permissions** tab as a table where each cell contains R/W/D checkboxes. Changes are saved on each checkbox toggle. `SYSTEM_ADMIN` cells are locked (always full access).

---

## 15. Multi-Company Context Switcher (Tech Admin)

When a Tech Admin is logged in, the Admin Panel header shows a company dropdown:

```
Company context: [ All Companies ▾ ]   [Scoped]
```

Selecting a company POSTs to `/api/admin/switch-company` which stores the company UUID in `session['admin_company_id']`. All subsequent API calls from the admin panel (users, employees, BUs, locations, FUs) then filter to that company. Selecting "All Companies" clears the filter.

The switcher also reloads all live data in the current active tab via `switchCompanyCtx()` in the browser JS.

---

## 16. Login Page

The login page uses a **two-column split-panel layout**:

- **Left panel** — dark gradient hero with product branding, tagline, and four feature highlights.
- **Right panel** — white form panel with demo account chips (2-column grid, click-to-auto-login), email input, and submit button.

Critical asset path: the stylesheet must be referenced as `filename='css/style.css'` (not `filename='style.css'`). This is verified by `tests/test_ui_ux.py::TestTemplateAssetConsistency::test_no_template_uses_bare_style_css`.

---

## 17. DB Setup Script

`scripts/setup_db.py` is a one-shot, safe-to-re-run setup script that:

1. **Applies schema migration** — adds `company_id` to `business_units`, `locations`, `functional_units`; creates `PORTAL_ADMIN` role; creates `portal_features` and `role_feature_access` tables.
2. **Backfills company_id** on existing org table rows by looking at which company the employees assigned to each BU/location/FU belong to.
3. **Removes Tech Admin from company** — sets `company_id = NULL` on all `SYSTEM_ADMIN` employee records.
4. **Seeds portal features** and default role–feature access permissions.
5. **Seeds Telia employees** — 100 employees with full org hierarchy, user accounts, manager relationships, using the live Telia company UUID from the DB.

```bash
python scripts/setup_db.py
```

---

## 18. Telia Company Seed Data

`database/telia_seed.sql` and `scripts/setup_db.py` seed the Telia Company with:

| Entity | Count | Detail |
|--------|-------|--------|
| Business Units | 5 | Technology & Innovation, Commercial & Sales, Finance & Administration, People & Culture, Network & Operations |
| Locations | 5 | Stockholm HQ, Helsinki, Oslo, Copenhagen, Tallinn |
| Functional Units | 12 | Distributed across BUs |
| Employees | 100 | L1–L6 (Junior → C-Suite) with Nordic names |
| Manager hierarchy | Full | 4 levels: C-suite → VP → Senior Manager → IC |
| Portal accounts | 100 | All employees receive a user account |
| Portal Admin | 1 | Maria Andersson (CPO) seeded as `PORTAL_ADMIN` |

The raw SQL seed (`telia_seed.sql`) uses hardcoded UUIDs and requires the Telia company to exist with exactly those UUIDs. The Python script (`setup_db.py`) is the recommended path as it dynamically looks up the actual Telia company UUID from the database.


---

## 19. In-App Notification System

### 19.1 Data Model

```sql
CREATE TABLE user_notifications (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type    VARCHAR(60) NOT NULL,   -- see the event vocabulary in 19.3
    message       TEXT NOT NULL,
    link          TEXT,                   -- /vacation | /vacation/team | /org-change
    is_read       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- What this notification is ABOUT, so it can be retired when that thing is
    -- decided (migration 09, DEF-003). Polymorphic and deliberately without a
    -- foreign key: a notification must outlive the entity it describes, and the
    -- column points at several subsystems.
    related_type  VARCHAR(40),            -- e.g. 'ORG_CHANGE_REQUEST'
    related_id    UUID
);
CREATE INDEX idx_user_notif_user_unread ON user_notifications(user_id, is_read, created_at DESC);
-- Partial: the resolve path only ever touches unread rows.
CREATE INDEX idx_user_notifications_related_unread
    ON user_notifications (related_type, related_id) WHERE NOT is_read;
```

### 19.1a Calls to action vs. receipts vs. outcomes

A notification is one of three things, and the distinction is load-bearing:

| Kind | Example event | Retired when the entity is decided? | Icon |
|---|---|---|---|
| **Call to action** | `ORG_CHANGE_REQUESTED` ("awaiting your approval") | **Yes** — `resolve_related()` | ⏳ |
| **Receipt** | `ORG_CHANGE_SUBMITTED` ("your request was submitted") | No — it is the requester's record | 📨 |
| **Outcome** | `ORG_CHANGE_APPROVED` / `ORG_CHANGE_REJECTED` | No — the user has not seen it yet | ✅ / ❌ |

`notification_service.resolve_related(related_type, related_id, event_types)` marks the matching
unread rows read. `org_change_service` calls it on **reject, level advance, final approval and
cancel**, always *before* writing the next announcement — retiring afterwards would sweep away the
notification just created for the next level. Several users can hold an approving role, so retiring
per-entity (not per-user) is the point: the approver who never opened the bell must also stop being
asked (DEF-003).

**Icon rule (DEF-002).** `templates/base.html` maps `event_type → icon` explicitly via `NOTIF_ICON`,
with a neutral 🔔 fallback. Never derive a status icon from a single-event comparison
(`x === 'VACATION_APPROVED' ? '✅' : '❌'`): every other event on the system then inherits the failure
icon, and an item with no outcome yet renders as a refusal.

### 19.2 Service Layer (`app/services/notification_service.py`)

| Function | Purpose |
|---|---|
| `create_user_notification(user_id, event_type, message, link)` | Inserts one unread notification row |
| `get_unread_notifications(user_id, limit=20)` | Returns list of unread rows |
| `get_unread_count(user_id)` | Returns integer count of unread rows |
| `mark_all_read(user_id)` | Sets `is_read=TRUE` for all unread rows |

### 19.3 Bell Notification (base.html)

The topbar bell is shown to **all authenticated users** (not just managers). Badge count = pending approvals + unread notifications.

```javascript
const [pendingRes, notifRes] = await Promise.all([
    fetch('/api/vacation/pending-count'),
    fetch('/api/my-notifications'),
]);
const total = pending + notifCount;
```

Dropdown has two sections:
- **Pending Approvals** (managers only, rendered in Jinja2 with `{% if has_role(...) %}`)
- **My Notifications** (everyone — approved/rejected/cancelled alerts)

Notifications auto-mark as read 2 s after dropdown opens.

### 19.4 Trigger Points

| Event | Where triggered | Recipient |
|---|---|---|
| Vacation APPROVED | `api_vacation_review` (approve) | Employee |
| Vacation REJECTED | `api_vacation_review` (reject) | Employee |
| Vacation CANCELLED/WITHDRAWN | `api_vacation_cancel` | Manager |

All triggers are best-effort (`try/except Exception: pass`) so they never break the core action.

### 19.5 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/my-notifications` | GET | Returns `{count, notifications:[]}` for current user |
| `/api/my-notifications/mark-read` | POST | Marks all as read for current user |

---

## 20. Vacation Cancellation & Withdrawal

### 20.1 Rules

| Request Status | Start Date | Action allowed |
|---|---|---|
| PENDING | Any | Cancel (always) |
| APPROVED | > today | Withdraw |
| APPROVED | ≤ today | Blocked (400) |
| REJECTED / CANCELLED | Any | Blocked (400) |

### 20.2 Endpoint

`DELETE /api/vacation/request/<req_id>`

The single endpoint handles both cancel and withdraw. The business rule check:

```python
if status == 'PENDING':
    pass  # always cancellable
elif status == 'APPROVED':
    if start <= datetime.date.today():
        return jsonify({'error': 'Cannot withdraw a request that has already started.'}), 400
else:
    return jsonify({'error': 'Only PENDING or future APPROVED requests can be cancelled.'}), 400
```

### 20.3 UI

- PENDING rows: red `btn btn-danger btn-sm` "✕ Cancel" button
- APPROVED future rows: ghost danger "Withdraw" button
- Both show confirmation dialogs mentioning manager notification
- `today` passed from Flask route to template for Jinja comparison

---

## 21. Analytics & Reporting Dashboard

### 21.1 Data Collection

**Page Views** (`page_views` table):
- Logged by `app/services/page_tracker.py` via `@app.after_request`
- Background thread — zero request latency added
- Skips: `/api/`, `/static/`, login/logout, unauthenticated requests
- Normalises dynamic routes (e.g. `/profile/123` → `/profile`)

**Search Queries** (`search_logs` table):
- Logged in `app/routes/search.py::api_search()` via background thread
- Stores: `query`, `result_count`, `role`, `company_id`

### 21.2 Service Layer (`app/services/analytics_service.py`)

| Function | Returns |
|---|---|
| `get_overview(company_id, start, end)` | DAU, top pages, feature adoption %, bulk import stats |
| `get_vacation_analytics(company_id, start, end, group_by)` | KPIs, over-time series, by-type, utilisation, drilldown |
| `get_skills_analytics(company_id, start, end)` | Completeness %, validation rate, top skills, per-employee table |
| `get_org_analytics(company_id, start, end)` | Headcount KPIs, span of control, org depth, org chart usage |
| `get_search_analytics(company_id, start, end)` | Top terms, zero-result rate, volume over time |

### 21.3 API Routes (`app/routes/analytics.py`)

| Route | Access |
|---|---|
| `GET /admin/analytics` | Page — SYSTEM_ADMIN, PORTAL_ADMIN, HR_ADMIN |
| `GET /api/analytics/overview` | SYSTEM_ADMIN, PORTAL_ADMIN, HR_ADMIN |
| `GET /api/analytics/vacation?group_by=company\|department\|location\|manager` | Same |
| `GET /api/analytics/skills` | Same |
| `GET /api/analytics/org` | Same |
| `GET /api/analytics/search` | Same |
| `GET /api/analytics/export/csv?section=<tab>` | Same |

Company scoping: PORTAL_ADMIN and HR_ADMIN always use `session['company_id']`; SYSTEM_ADMIN uses `?company_id=` param.

### 21.4 Date Range

`?range=30d|90d|365d` or `?start=YYYY-MM-DD&end=YYYY-MM-DD`. Falls back to 30d on invalid custom dates.

### 21.5 Frontend

- Chart.js 4.4.3 via CDN
- Tab switching is JS-driven; each tab fetches data once (cached per filter state)
- Filter changes (`_loaded = {}`) force full reload
- All filter params in URL via `history.replaceState` (shareable links)
- Print CSS hides navigation; all tab content visible in print mode

### 21.6 Export

- **CSV**: `GET /api/analytics/export/csv?section=<tab>&range=<range>` — Python `csv.DictWriter` → `text/csv` response with `Content-Disposition: attachment`
- **PDF**: Browser `window.print()` with `@media print` CSS


---

## 22. Position Change Workflow (Org-Change Engine)

Drag-and-drop, multi-level, sequential approval for moving an employee's business unit,
functional unit, location and reporting manager. Generalises the single-level vacation
approval into a configurable N-step chain.

### 22.1 Components

| Layer | File | Role |
|-------|------|------|
| Schema | `database/migrations/06_org_change_workflow.sql` | 4 tables + `org_change` feature (§3.5) |
| Engine | `app/services/org_change_service.py` | create / decide / apply / notify + config |
| Routes | `app/routes/org_change.py` | request lifecycle, inbox, prefill, admin config |
| Dialog | `templates/org_change/_move_modal.html` | the **one** Request Position Change dialog, shared by every entry point |
| Drag-drop | `templates/org/tree.html` | draggable cards (gated by `can_move`); includes the dialog |
| Transfer… | `templates/employees/profile.html`, `templates/employees/directory.html` | the task-oriented entry point (KAN-185, §22.5a) |
| Inbox | `templates/org_change/inbox.html` | Pending My Approval + My Requests tabs |
| Config | `templates/admin/org_change_workflow.html` | ordered step editor (role or person) |
| Nav | `templates/base.html` | "Position Changes" + "Change Workflow" links |

### 22.2 Engine logic (`org_change_service.py`)

- `workflow_steps(company_id)` — ordered steps; **falls back to a single `HR_ADMIN` step** when a company has no configured chain.
- `create_request(...)` — snapshots the subject's current placement (BU/FU/location/manager), inserts the request + one `org_change_approvals` row per step **in one transaction** (a request with a partial chain would be approvable in fewer levels than configured), then notifies step-1 approvers and the requester **after** it commits.
- `decide(request_id, user, decision, note)` — verifies the caller is eligible for the **current** step (`_user_matches_step`: role held, or employee id equals the named approver), then, in **one transaction per outcome**, records the step decision plus what it triggers:
  - **reject** → `status=REJECTED`, chain stops, notify requester + subject;
  - **approve, more steps** → `current_step += 1`, notify next approvers + requester;
  - **approve, last step** → the decision, `_apply_change()` and `status=APPROVED` commit together (KAN-155 / TD-7), then notify requester + subject.
  Any failure inside the block leaves the request PENDING with the step undecided and the employee's placement untouched.
- `apply_change(request)` — atomic standalone entry point; wraps `_apply_change()` in a transaction. `_apply_change()` sets the old `employee_org_assignments.is_current=FALSE` (`effective_to=today`), inserts a new current row, and re-points the `SOLID_LINE` `manager_relationships` row if the manager changed. `decide()` calls `_apply_change()` directly because it already holds the transaction — `transaction()` must never be nested. Mirrors the registration logic in `admin.py` (which is **not** yet atomic — see §4.2a).
  > **The new row is the old row overlaid with what changed.** A request stores only the fields the requester actually altered; the rest are `NULL`, and `NULL` means *no change*, **not** *clear this*. `_apply_change()` therefore carries location, business unit, functional unit and cost centre forward from the outgoing assignment and overlays the proposed values. **This was a live data-loss defect** (found by driving the approval chain in a browser, Aug 2026): only the cost centre was carried, so approving a business-unit-only move silently erased the employee's location **and** functional unit. Every existing test passed a fully-populated proposal, which is why none caught it. KAN-185 made it far more likely to fire — the Transfer… dialog starts every select at *— No change —*, so partial proposals became the normal case rather than the exception. Regression coverage: `TestApplyCarriesUnchangedFieldsForward` in `tests/test_org_change.py` (BU-only, location-only, manager-only, full proposal, and an employee with no prior assignment).
- `save_workflow(...)` — replace-all of the company's chain, in one transaction: a partial rewrite would silently change who can approve.
- Approver resolution: `_step_approver_user_ids` returns all active company users holding the step's role, or the single user behind the named employee.

### 22.3 Authorisation

- Pages/APIs gated by `@require_feature_access('org_change', ...)`; config gated by `@require_feature_access('org_structure','w')` — no hardcoded role lists (per `CLAUDE.md`).
- **Initiator business rule** (on top of the feature gate): the requester must be the subject's current solid-line manager **or** hold `HR_ADMIN` / `PORTAL_ADMIN` / `SYSTEM_ADMIN`. Plain `EMPLOYEE` can never self-initiate.

### 22.4 Notifications

In-app bell notifications via `notification_service.create_user_notification` (link `/org-change`).
Event types: `ORG_CHANGE_REQUESTED`, `ORG_CHANGE_STEP_APPROVED`, `ORG_CHANGE_APPROVED`,
`ORG_CHANGE_REJECTED`, `ORG_CHANGE_CANCELLED`. (Email dispatch is out of scope for v1 — no
per-company `notification_settings`/template rows are seeded for these events yet.)

### 22.5 Drag-and-drop (frontend)

`org_tree()` passes `can_move = can_access_feature('org_change','w')`. When true, each `.ft-card`
becomes `draggable`; dropping card **S** onto card **T** calls `openMoveModal(S, T)`, which fetches
`/api/org-change/prefill` to pre-fill the new manager (= T) and T's unit/location, all overridable via
company-scoped selects, plus a mandatory reason. Submit → `POST /api/org-change/request`.

### 22.5a Transfer… entry point (KAN-185)

A transfer **is** a position change, so it is a second *entry point* — never a second system. There is
no `/transfer` page, no `POST /api/transfer`, no transfer table and no `transfer` feature code; the
word "Transfer" appears only on the affordance, and the dialog it opens says *Request Position Change*.

Three entry points, one dialog (`_move_modal.html`), one endpoint (`POST /api/org-change/request`),
one engine:

| Entry point | Opener | Prefilled from |
|---|---|---|
| Org-tree drag-and-drop | `openMoveModal(S, T)` | the drop target **T**'s placement |
| Employee profile | `openTransferModal(...)` | the subject's **own** placement — every select starts at "no change" |
| Directory row `⋯` menu | `openTransferModal(...)` | as above |

Each is gated by **four** conditions: `org_change` write access, the initiator rule, an `ACTIVE`
subject, and not-your-own-record. The profile computes this server-side in
`employees._can_transfer()`, which **borrows** `org_change.can_initiate_org_change_for()` rather than
re-implementing the rule. The directory renders rows client-side, so the route passes
`can_transfer_any` / `viewer_employee_id` and the per-row rule compares the row's existing
`solid_manager_id`. **All of this is display only** — `POST /api/org-change/request` re-checks the
feature gate, `_can_initiate_for`, the ACTIVE status and company scope on every call.

The dialog also blocks before submit on: a no-op move, an existing PENDING request for the subject
(one at a time — a second would carry a stale "from" snapshot), a non-ACTIVE subject or proposed
manager, a reporting cycle, and any BU/FU/location/manager belonging to another company. It shows the
company's configured approval chain (read from `workflow_steps`, so it can never describe a chain the
engine would not build) and warns that direct reports do **not** move with a manager.

> **`AC-185-07` effective-dating is not implemented and is deliberately absent from the UI.**
> `org_change_requests` has no column for an effective date and `create_request()` takes no such
> parameter, so rendering the field would silently discard what the user typed. Blocked pending a
> schema decision (CFL-4).

Because the drag is a pointer-only interaction, the org-tree legend names the keyboard equivalent —
"open a person's profile and choose Transfer…" (WCAG 2.1.1 / 2.5.7).

### 22.6 Tests

`tests/test_org_change.py` (18 tests): initiator permission matrix (employee blocked, manager
limited to own reports, HR/Portal unrestricted), sequential `decide` (advance / reject-stops /
final-applies), approver eligibility, `apply_change` SQL (assignment + conditional manager re-point),
`create_request` notifications, workflow-config save, and the **transaction boundaries** (KAN-155):
each path opens exactly one committed unit of work, every write happens inside it, notifications fire
only after it commits, and a failed final approval commits nothing and notifies nobody.

`tests/test_transfer_entry_point.py` (59 tests) is the **anti-bypass suite** for KAN-185. The risk in
that story is not building it — it is someone building a *second path* — so the suite asserts, by
inspecting the route module as well as exercising it: the route module contains no SQL writes and
does not even import `execute`/`insert_returning`; nothing is applied at creation or before the final
approval; a single rejection applies nothing; approvals stay strictly sequential; every read and
write is company-scoped and a foreign UUID posted straight at the API is refused; `employees.company_id`
is never modified; and both entry points produce **identical** engine calls. It also pins the display
gates, including that the profile handler survives quotes in a name — an escaped-attribute bug that a
naive substring assertion missed. Full suite: **4,627 passing**; browser 84/84, vacation 39/39.

---

## 23. Audit Trail — `audit_log` + `audit_service` (EP38 / KAN-187, ADR-009)

One append-only, company-scoped trail for the whole platform. Schema in **§3.6**; the service is
`app/services/audit_service.py` and is the **only** write path into the table.

### 23.1 API

```python
from app.services import audit_service as audit

audit.record(action, entity_type, entity_id, *, company_id, actor, reason,
             before=None, after=None,
             subject_employee_id=None, subject_employee_number=None,
             correlation_id=None, outcome='SUCCESS', error_code=None,
             metadata=None, retention_class='STANDARD',
             actor_ip=None, actor_session_id=None)          -> None
audit.record_many(entries)                                   -> None
audit.entity_timeline(company_id, entity_type, entity_id, limit=50, offset=0)
audit.company_timeline(company_id, *, action=None, actor_user_id=None,
                       correlation_id=None, since=None, until=None,
                       limit=50, offset=0)
audit.new_correlation_id()                                   -> str
```

`actor` is the same light dict the org-change engine uses —
`{'user_id', 'employee_id', 'roles', 'company_id'}`, optionally `user_name` / `user_email` so
`actor_label` can be built. Do not invent a second actor shape.

### 23.2 The load-bearing property — it joins the caller's transaction

`record()` **never opens a connection and never commits.** It writes through `app.db.execute` on the
request-scoped `g.db`, so it runs inside whatever `transaction()` the caller already has open (§4.2a).
`transaction()` refuses to nest, so audit **must not** open one of its own.

```python
with transaction():                          # opened by the CALLER, once
    execute("UPDATE employees SET employment_status='TERMINATED' ...")
    audit.record('EMPLOYEE_STATUS_CHANGED', 'employee', emp_id,
                 company_id=company_id, actor=actor,
                 reason='End of fixed-term contract',
                 before={'employment_status': 'ACTIVE'},
                 after={'employment_status': 'TERMINATED'},
                 correlation_id=cid)
# both durable, or neither
```

The audit row commits atomically with the change it describes, and a rolled-back change takes its audit
row with it. **A false audit entry is worse than a missing one.**

Corollary: **failed and rejected attempts are not in `audit_log`** when they roll back — authorisation
denials and validation failures belong in the application log. A `FAILED` row (`outcome='FAILED'`,
`error_code=...`) can only be written **after** the failed transaction has already rolled back, where
`execute()` is back in autocommit.

### 23.3 Rules the service enforces at runtime

| Rule | Behaviour |
|---|---|
| `action` is a closed enumeration | Anything outside `audit_service.ACTIONS` raises `AuditError` |
| `company_id` is mandatory | Comes from the **affected entity**, never the session or request input. When a SYSTEM_ADMIN acts cross-tenant the row lands in the *affected* tenant's trail |
| `reason` is mandatory | Non-blank, enforced in the service **and** by a DB CHECK |
| Diffs only, never whole rows | `before` / `after` must be **flat** maps of `field -> scalar`; nested structures raise (that is how a whole row gets smuggled in) |
| Both sides describe the same fields | Mismatched key sets raise — a row holds a field-level **diff**, not two snapshots |
| No secrets, ever | Keys containing `password`, `token`, `secret`, `api_key`, `private_key`, `salt`, `credential` … are refused in `before`/`after` **and** `metadata` |
| Subject is id + employee number | There is no column and no parameter for the subject's name |
| `record_many` validates the whole batch first | A malformed entry cannot leave a half-written set behind |
| Reads are company-scoped | Both timelines filter `company_id = %s::uuid` **only** — never `OR company_id IS NULL` |

### 23.4 Correlation ids

One unit of work = one correlation id. Generate it once with `new_correlation_id()` and pass it to every
row so `company_timeline(company_id, correlation_id=cid)` returns the whole story in order.

### 23.5 Tests

`tests/test_audit_service.py` (44 tests), three tiers:

- **Contract** — the twelve required fields, the closed enumeration, mandatory `company_id` / `reason`,
  diff-shape and secret rejection, subject-never-named.
- **Transaction mechanics** (fake connection, reusing `tests/test_transactions.FakeConnection`) —
  `record()` commits nothing inside the caller's block, opens no transaction of its own, and a
  rolled-back change leaves no audit row.
- **Real Postgres** — atomic commit with the audited change; rollback leaves nothing; the append-only
  trigger rejects both a targeted and a blanket `UPDATE`; `company_id` NOT NULL and the blank-reason
  CHECK are enforced by the database; one tenant never sees another's rows; and the migration **applies,
  re-applies, reverses and re-applies** on a genuinely fresh database built from `schema.sql`.
