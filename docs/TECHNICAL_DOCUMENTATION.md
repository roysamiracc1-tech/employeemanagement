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

## 4. Application Architecture

### 4.1 Request Lifecycle

```
Browser → Flask Route
            │
            ├─ @login_required / @require_roles decorator
            │     └─ checks session['user_id'] and session['roles']
            │
            ├─ get_db() → psycopg2 connection (stored in Flask g)
            │
            ├─ query() / execute() / insert_returning()
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
| `query(sql, params, one)` | SELECT; returns list of dicts or single dict |
| `execute(sql, params)` | INSERT/UPDATE/DELETE with auto-commit |
| `insert_returning(sql, params)` | INSERT … RETURNING id; returns first row as dict |
| `to_dict(row)` | Converts RealDictRow; serialises datetime → ISO, Decimal → float |
| `_next_employee_number()` | Computes next EMP-NNN from current MAX |
| `_vacation_types_for_employee(emp_id)` | Location filter + rule evaluation |
| `_employee_solid_manager(emp_id)` | Returns solid-line manager UUID |
| `_used_days(emp_id, vt_id, year)` | Sums PENDING+APPROVED working days for year |
| `_save_logo(file_storage, old_url)` | Saves uploaded logo, cleans up old file |
| `_build_nested(flat)` | Converts flat CTE rows → nested tree dict |

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
| GET | `/api/org-tree?root=<id>` | Recursive tree from root (empty = full org) |
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

## 7. Org Tree Algorithm

Uses a PostgreSQL **recursive CTE** limited to 10 levels:

```sql
WITH RECURSIVE tree AS (
    -- Base case: selected root employees
    SELECT e.id, ..., NULL::uuid AS manager_id, 0 AS depth
    FROM employees e
    WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE'

    UNION ALL

    -- Recursive case: find employees whose SOLID_LINE manager is already in tree
    SELECT e.id, ..., mr.manager_id, t.depth + 1
    FROM employees e
    JOIN manager_relationships mr ON mr.employee_id = e.id
        AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
    JOIN tree t ON t.id = mr.manager_id
    WHERE e.employment_status = 'ACTIVE' AND t.depth < 10
)
SELECT id::text, ..., manager_id::text, depth FROM tree
```

`_build_nested(flat)` converts the flat ordered list into a nested `{..., children: [...]}` structure consumed by the client-side `buildNode()` recursive DOM builder.

For **Full Org** view (admin, no root selected), the base case uses all employees with no current SOLID_LINE manager.

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

## 9. Security Considerations

| Area | Implementation |
|------|---------------|
| **Route protection** | `@login_required` + `@require_roles(*roles)` decorators on every non-public route and API |
| **Session integrity** | Flask server-side session; `SECRET_KEY` from env var |
| **XSS** | Jinja2 auto-escapes all template variables; `| safe` used only for admin-controlled `header_html` / `footer_html` |
| **SQL injection** | All DB calls use parameterised queries via psycopg2; no string formatting in SQL |
| **File uploads** | Extension allowlist; UUID filename (no user-controlled path); size validated client-side |
| **IDOR prevention** | Profile self-edit APIs check `session['employee_id']`; vacation cancel checks `employee_id` ownership; skill validation requires admin role |
| **CSRF** | Not yet implemented — forms rely on session cookies; recommended addition for production |
| **Passwords** | Not implemented in dev; production should add bcrypt hashing and password field |

---

## 10. Deployment Notes

### Environment Variables
```bash
SECRET_KEY=<random-256-bit-string>
PGHOST=localhost
PGPORT=5432
PGDATABASE=employee
PGUSER=<db-user>
PGPASSWORD=<db-password>
```

### Running the Server
```bash
python run.py                               # dev mode, port 8000
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"   # production
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
The test suite uses **pytest** and **pytest-flask**. All DB calls are mocked with `unittest.mock` — no live PostgreSQL connection is required to run tests.

```bash
pip install pytest pytest-flask
python -m pytest           # run all tests
python -m pytest -v        # verbose output
python -m pytest tests/test_helpers.py   # single file
```

### Test Structure

```
tests/
├── conftest.py                  # Fixtures: app, client, auth/admin/manager sessions, sample data
├── test_db.py                   # serialize() and to_dict() helpers
├── test_helpers.py              # Business logic and pure functions
├── test_auth.py                 # Auth decorators and login/logout routes
├── test_routes_employees.py     # Employee directory, profile, self-edit APIs
├── test_routes_vacation.py      # Vacation submit, cancel, review workflow
└── test_routes_admin.py         # Admin panel, user/role management, company admin
```

### Test Coverage Summary

| File | Tests | What is covered |
|------|-------|----------------|
| `test_db.py` | 13 | `serialize()` — date, datetime, Decimal, primitives; `to_dict()` — type conversion |
| `test_helpers.py` | 39 | `rule_label`, `build_nested` (tree construction, orphan nodes, multi-root), `next_employee_number`, `employee_solid_manager`, `used_days`, `is_direct_report`, vacation eligibility engine (gender rules, tenure rules, AND logic, no-rules case, rule_labels attached), `save_logo` (extension validation, file save, old file cleanup) |
| `test_auth.py` | 18 | `@login_required` redirect, `@require_roles` per-role access, login form, unknown email error, logout session clear |
| `test_routes_employees.py` | 24 | Directory (role gating), profile (own / other / not-found), my-team, `/api/employees` role-filtered responses, profile self-edit APIs (skills, certs, gender, theme toggle) |
| `test_routes_vacation.py` | 20 | Vacation page load, submit (no manager, missing fields, ineligible type, end-before-start, annual limit exceeded, success), cancel (not-found, non-pending, success), review (invalid action, not-found, already-actioned, approve, reject) |
| `test_routes_admin.py` | 16 | Admin panel access, register user (form load, missing name, duplicate email), user list, update roles, toggle user, validate skill, company list/new |
| **Total** | **130** | |

### Key Fixtures (conftest.py)

| Fixture | Description |
|---------|-------------|
| `client` | Unauthenticated Flask test client |
| `auth_client` | Client with `EMPLOYEE` session |
| `admin_client` | Client with `SYSTEM_ADMIN` + `EMPLOYEE` session |
| `manager_client` | Client with `SOLID_LINE_MANAGER` + `EMPLOYEE` session |
| `SAMPLE_EMPLOYEE` | Reusable employee dict for mocking `fetch_employees` |
| `SAMPLE_VACATION_TYPE` | Reusable vacation type dict for mocking |

### Testing Strategy

- **Pure functions** (`rule_label`, `build_nested`, `serialize`, `to_dict`) — called directly, no mocking needed.
- **DB-dependent helpers** — `app.helpers.query` / `app.db.query` patched via `unittest.mock.patch`.
- **Flask routes** — tested via `app.test_client()` with session pre-seeded; all DB calls in route modules patched individually.
- **Auth enforcement** — verified by checking 302 redirect for unauthenticated / unauthorised requests, 200 for authorised ones.

