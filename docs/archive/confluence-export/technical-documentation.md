<!--
  FROZEN CONFLUENCE EXPORT — DO NOT EDIT.
  Source: https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/360451
  Page ID 360451 · last edited in Confluence 18 May 2026 · exported 8 Aug 2026.
  SUPERSEDED BY: docs/TECHNICAL_DOCUMENTATION.md (22 sections vs the 10 below) — read that instead.
-->

# HR Portal — Technical Documentation

## 1. System Overview

| Layer | Technology |
| --- | --- |
| Backend | Python 3 · Flask 3.x |
| Database | PostgreSQL 14+ with uuid-ossp extension |
| DB Driver | psycopg2 with RealDictCursor |
| Frontend | Server-rendered Jinja2 · Vanilla JS · CSS custom properties |
| Auth | Server-side session (Flask session, 8-hour TTL) |

## 2. Project Structure

```
employeemanagement/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # DB config, app settings
│   ├── db.py             # query/execute/insert_returning helpers
│   ├── auth.py           # login_required, require_roles, require_feature_access, context processor
│   ├── helpers.py        # fetch_employees, vacation engine, org tree CTE, save_logo
│   └── routes/
│       ├── auth.py       # login / logout
│       ├── dashboard.py  # dashboard + stats API
│       ├── employees.py  # directory, profile, my_team + APIs
│       ├── admin.py      # admin panel + register user + APIs
│       ├── org.py        # org tree + API
│       ├── company.py    # company view + admin company management
│       ├── vacation.py   # all vacation routes
│       ├── analytics.py  # analytics routes + APIs
│       └── skills_intelligence.py  # skills intelligence routes + APIs
├── templates/
│   ├── base.html  login.html  dashboard.html
│   ├── admin/     employees/  org/  company/  vacation/
├── static/
│   ├── css/style.css
│   └── uploads/logos/
├── database/
│   ├── schema_v2.sql  seed_data.sql
│   └── migrations/
├── tests/
│   ├── conftest.py
│   ├── test_db.py
│   ├── test_helpers.py
│   ├── test_auth.py
│   ├── test_routes_employees.py
│   ├── test_routes_vacation.py
│   ├── test_routes_admin.py
│   ├── test_routes_analytics.py
│   ├── test_routes_skills_intelligence.py
│   ├── test_regression.py
│   ├── test_access_matrix.py
│   ├── test_permission_matrix.py
│   ├── test_api_input_validation.py
│   ├── test_auth_comprehensive.py
│   ├── test_company_scoping.py
│   ├── test_employee_comprehensive.py
│   ├── test_helpers_comprehensive.py
│   ├── test_analytics_comprehensive.py
│   ├── test_si_comprehensive.py
│   ├── test_vacation_comprehensive.py
│   ├── test_business_logic_bulk.py
│   ├── test_data_validation_bulk.py
│   └── test_session_state_bulk.py
├── docs/
├── run.py
├── pytest.ini
└── requirements.txt
```

## 3. Database Schema

### 3.1 Core Tables

**companies** — Legal entity. All employees, vacation types, and branding belong to one company.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | Auto-generated |
| name | VARCHAR(200) | Unique company name |
| theme_color | VARCHAR(7) | Hex colour, default #2563eb |
| header_html | TEXT | Raw HTML injected above all pages |
| footer_html | TEXT | Raw HTML injected below all pages |
| logo_url | TEXT | Uploaded path or external URL |
| is_active | BOOLEAN | Inactive companies cannot receive new employees |

**employees** — Core person record.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK |  |
| employee_number | VARCHAR(50) UNIQUE | Auto-generated EMP-001 … EMP-NNN |
| employment_status | VARCHAR(50) | ACTIVE / INACTIVE / RESIGNED / TERMINATED |
| employment_type | VARCHAR(50) | PERMANENT / CONTRACTOR / INTERN / PART_TIME |
| join_date | DATE | Used for tenure calculations and anniversary badges |
| gender | VARCHAR(10) | MALE / FEMALE / OTHER; drives vacation eligibility |
| company_id | UUID FK | References companies |

**users** — Portal login account; 1-to-1 with employee.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK |  |
| employee_id | UUID FK UNIQUE |  |
| email | VARCHAR(255) UNIQUE | Login credential |
| is_active | BOOLEAN | Admins can disable login |
| theme_preference | VARCHAR(10) | light / dark; persisted per user |

### 3.2 Org Structure

```
companies
  └── business_units (company_id FK)
        └── functional_units (business_unit_id FK)
  └── locations (company_id FK)
  └── cost_centers (company_id FK)

employee_org_assignments
  employee_id, location_id, business_unit_id,
  functional_unit_id, cost_center_id
  is_current BOOLEAN ← only one current assignment per employee
```

**manager_relationships**

| Column | Type | Notes |
| --- | --- | --- |
| employee_id | UUID FK | The subordinate |
| manager_id | UUID FK | The manager |
| relationship_type | VARCHAR | SOLID_LINE / DOTTED_LINE |
| is_current | BOOLEAN | Only current records used in queries |

### 3.3 Vacation Tables

```
vacation_types (company_id FK)
  ├── vacation_type_locations  ← zero rows = company-wide; rows = location-scoped
  └── vacation_type_rules      ← eligibility rules (AND logic)
        rule_type: GENDER_EQ | MIN_TENURE_MONTHS | MIN_TENURE_YEARS

vacation_requests
  employee_id, vacation_type_id, manager_id,
  start_date, end_date, working_days,
  status: PENDING | APPROVED | REJECTED | CANCELLED
  manager_note TEXT
```

## 4. Application Architecture

### 4.1 Key Helper Functions

| Function | Purpose |
| --- | --- |
| query(sql, params, one) | SELECT; returns list of dicts or single dict |
| execute(sql, params) | INSERT/UPDATE/DELETE with auto-commit |
| insert_returning(sql, params) | INSERT … RETURNING id; returns first row as dict |
| to_dict(row) | Converts RealDictRow; serialises datetime → ISO, Decimal → float |
| next_employee_number() | Computes next EMP-NNN from current MAX |
| vacation_types_for_employee(emp_id) | Location filter + rule evaluation |
| employee_solid_manager(emp_id) | Returns solid-line manager UUID |
| used_days(emp_id, vt_id, year) | Sums PENDING+APPROVED working days for year |
| save_logo(file_storage, old_url) | Saves uploaded logo, cleans up old file |
| build_nested(flat) | Converts flat CTE rows → nested tree dict |

### 4.2 Session Keys

| Key | Type | Set by |
| --- | --- | --- |
| user_id | str (UUID) | login |
| employee_id | str (UUID) | login |
| roles | list\[str\] | login |
| theme_pref | light or dark | login; updated by /api/user/theme |
| branding | dict | login; updated by admin_company_edit |
| admin_company_id | str (UUID) or None | SA company context switcher |

## 5. API Reference

### Authentication

| Method | Path | Description |
| --- | --- | --- |
| GET/POST | /login | Login form |
| GET | /logout | Clear session |
| POST | /api/user/theme | Save light/dark preference |

### Profile APIs

| Method | Path | Description |
| --- | --- | --- |
| POST | /api/profile/gender | Save gender |
| POST | /api/profile/skills | Add or update a skill |
| DELETE | /api/profile/skills/id | Remove a skill |
| POST | /api/profile/certifications | Add certification |
| PUT | /api/profile/certifications/id | Update certification |
| DELETE | /api/profile/certifications/id | Remove certification |

### Admin APIs

| Method | Path | Roles | Description |
| --- | --- | --- | --- |
| GET | /api/admin/users | SYSTEM_ADMIN, PORTAL_ADMIN | All users with roles |
| POST | /api/admin/update-roles | SYSTEM_ADMIN, PORTAL_ADMIN | Replace user role set |
| POST | /api/admin/toggle-user | SYSTEM_ADMIN, PORTAL_ADMIN | Enable/disable user |
| POST | /api/admin/validate-skill | SYSTEM_ADMIN, HR_ADMIN | Validate employee skill |
| GET | /api/admin/vacation-rules | SYSTEM_ADMIN | Rules for vacation type IDs |
| POST | /api/admin/switch-company | SYSTEM_ADMIN | Switch SA company context |
| GET | /api/admin/company/roles | SYSTEM_ADMIN, PORTAL_ADMIN | List company-specific roles |
| POST | /api/admin/company/roles | SYSTEM_ADMIN, PORTAL_ADMIN | Create company role |
| PUT | /api/admin/company/roles/id | SYSTEM_ADMIN, PORTAL_ADMIN | Update company role |
| DELETE | /api/admin/company/roles/id | SYSTEM_ADMIN, PORTAL_ADMIN | Delete company role |
| POST | /api/admin/company/roles/id/permissions | SYSTEM_ADMIN, PORTAL_ADMIN | Set role feature permissions |
| GET | /api/admin/company/role-feature-access | SYSTEM_ADMIN, PORTAL_ADMIN | Feature access matrix |
| POST | /api/admin/company/seed-admin-user | SYSTEM_ADMIN | Create first company admin |

### Vacation APIs

| Method | Path | Description |
| --- | --- | --- |
| POST | /api/vacation/request | Submit vacation request |
| DELETE | /api/vacation/request/id | Cancel own PENDING request |
| GET | /api/vacation/team-pending | Pending requests for reportees |
| GET | /api/vacation/team-upcoming | Upcoming approved leave |
| POST | /api/vacation/review/id | Approve or reject a request |

## 6. Vacation Eligibility Engine

Two-stage filtering:

**Stage 1 — SQL location filter:** Only types matching the employee's location (or company-wide types) are returned.

**Stage 2 — Python rule evaluation (AND logic):**

* GENDER_EQ: employee gender must match rule value
* MIN_TENURE_MONTHS: tenure in months must be >= rule value
* MIN_TENURE_YEARS: tenure in years must be >= rule value

Tenure computed as (today - join_date).days / 30.44 (months) and / 365.25 (years).

## 7. Org Tree Algorithm

PostgreSQL recursive CTE limited to 10 levels. Base case: selected root employees. Recursive case: employees whose SOLID_LINE manager is already in tree. `build_nested(flat)` converts the flat ordered list into a nested children structure for client-side rendering.

## 8. Security Considerations

| Area | Implementation |
| --- | --- |
| Route protection | @login_required + @require_feature_access decorators on every protected endpoint |
| Feature access | DB-driven two-tier permission system — role_feature_access + company_role_feature_access |
| Session integrity | Flask server-side session; SECRET_KEY from env var |
| XSS | Jinja2 auto-escapes all variables; safe filter only for admin-controlled HTML |
| SQL injection | All DB calls use parameterised queries via psycopg2 |
| File uploads | Extension allowlist; UUID filename; 2MB size limit |
| IDOR prevention | All self-edit APIs verify session employee_id ownership |
| Input validation | All API endpoints validate type + presence of required fields; non-string inputs rejected with 400 |

## 9. Deployment

### Environment Variables

```
SECRET_KEY=<random-256-bit-string>
PGHOST=localhost
PGPORT=5432
PGDATABASE=employee
PGUSER=<db-user>
PGPASSWORD=<db-password>
```

### Running the Server

```
python run.py                              # dev mode, port 8000
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"  # production
```

GitHub: https://github.com/roysamiracc1-tech/employeemanagement

## 10. Testing

### Overview

The test suite uses **pytest** and **pytest-flask**. All DB calls are mocked with `unittest.mock` — no live PostgreSQL connection is required to run the tests.

```
pip install pytest pytest-flask
python -m pytest          # run all 4,494 tests
python -m pytest -v       # verbose output
python -m pytest tests/test_regression.py   # regression suite only
```

**A pre-commit hook runs all 4,494 tests before every commit. No commit can land if any test fails.**

### Test Structure

```
tests/
├── conftest.py                      # Fixtures: app, client, auth/admin/manager sessions, sample data
├── test_db.py                       # serialize() and to_dict() helpers
├── test_helpers.py                  # Business logic and pure functions
├── test_auth.py                     # Auth decorators and login/logout routes
├── test_routes_employees.py         # Employee directory, profile, self-edit APIs
├── test_routes_vacation.py          # Vacation submit, cancel, review workflow
├── test_routes_admin.py             # Admin panel, user/role management, company admin
├── test_routes_analytics.py         # Analytics routes and scoping
├── test_routes_skills_intelligence.py  # SI routes and feature access
├── test_regression.py               # Documented invariants (past bugs, access rules)
│
│── Comprehensive parametrized suites ──────────────────────────────
├── test_access_matrix.py            # Every route × every role — 302/200 enforcement
├── test_permission_matrix.py        # Feature × role × R/W/D combinations
├── test_api_input_validation.py     # All POST/PUT/DELETE endpoints with bad inputs
├── test_auth_comprehensive.py       # _is_valid_uuid (200+ inputs), feature access combos
├── test_company_scoping.py          # Company isolation, cross-tenant prevention
├── test_employee_comprehensive.py   # Profile, directory, skills, certs — all roles
├── test_helpers_comprehensive.py    # Helper functions with parametrized inputs
├── test_analytics_comprehensive.py  # Analytics scoping, all roles × all endpoints
├── test_si_comprehensive.py         # SI scoping, feature gating, all roles
├── test_vacation_comprehensive.py   # Eligibility rules, review, calendar
├── test_business_logic_bulk.py      # rule_label, build_nested, UUID validation, tenure
├── test_data_validation_bulk.py     # Theme, gender, skills, cert API edge cases
└── test_session_state_bulk.py       # Session variations, multi-role combinations
```

### Test Coverage Summary

| File | Tests | What is covered |
| --- | --- | --- |
| test_db.py | 13 | serialize() — date, datetime, Decimal, primitives; to_dict() type conversion |
| test_helpers.py | 37 | rule_label, build_nested, next_employee_number, vacation eligibility, save_logo |
| test_auth.py | 18 | @login_required, @require_roles per-role access, login form, logout |
| test_routes_employees.py | 24 | Directory, profile, my-team, self-edit APIs |
| test_routes_vacation.py | 30 | Vacation page, submit, cancel, review, team views |
| test_routes_admin.py | 19 | Admin panel, register user, user list, roles, toggle |
| test_routes_analytics.py | 35 | Analytics routes, feature gating, scoping |
| test_routes_skills_intelligence.py | 23 | SI routes, enabled check, HR_ADMIN access |
| test_regression.py | 49 | Documented invariants — company role isolation, legacy HR bug prevention |
| test_access_matrix.py | 622 | Every route × every role — auth enforcement |
| test_permission_matrix.py | 461 | Feature × role × R/W/D combinations |
| test_api_input_validation.py | 458 | All endpoints with missing/invalid/malformed inputs |
| test_auth_comprehensive.py | 286 | \_is_valid_uuid 200+ inputs, can_access_feature, \_load_feature_access |
| test_company_scoping.py | 233 | Company isolation, current_company_id, viewer_company_id |
| test_employee_comprehensive.py | 225 | Profile cross-access, directory scoping, API edge cases |
| test_helpers_comprehensive.py | 201 | All helpers with parametrized inputs |
| test_analytics_comprehensive.py | 249 | Analytics scoping, ranges, roles |
| test_si_comprehensive.py | 278 | SI scoping, company access check, all roles |
| test_vacation_comprehensive.py | 211 | Eligibility rules, date validation, team calendar |
| test_business_logic_bulk.py | \~300 | rule_label, UUID validation, tenure boundary cases |
| test_data_validation_bulk.py | \~400 | Theme/gender/skill/cert input validation |
| test_session_state_bulk.py | \~350 | Session states, multi-role, company context variations |
| **Total** | **4,494** |  |

### Key Fixtures (conftest.py)

| Fixture | Description |
| --- | --- |
| client | Unauthenticated Flask test client |
| auth_client | Client with EMPLOYEE session |
| admin_client | Client with SYSTEM_ADMIN + EMPLOYEE session |
| manager_client | Client with SOLID_LINE_MANAGER + EMPLOYEE session |
| SAMPLE_EMPLOYEE | Reusable employee dict for mocking fetch_employees |
| SAMPLE_VACATION_TYPE | Reusable vacation type dict for mocking |

### Testing Strategy

* **Pure functions** (rule_label, build_nested, serialize, to_dict) — called directly, no mocking needed.
* **DB-dependent helpers** — app.helpers.query patched via unittest.mock.patch.
* **Flask routes** — tested via app.test_client() with session pre-seeded; all DB calls in route modules patched individually.
* **Auth enforcement** — verified by checking 302 redirect for unauthenticated / unauthorised requests, 200 for authorised ones.
* **Parametrized bulk tests** — @pytest.mark.parametrize used extensively to cover all role × route × input combinations with minimal boilerplate.

### Bugs Found and Fixed by Tests

The expanded test suite uncovered and fixed 6 production bugs:

| Endpoint | Bug | Fix |
| --- | --- | --- |
| POST /api/admin/update-roles | `AttributeError` when `user_id` is not a string or `roles` is not a list | Added `isinstance` guards; returns 400 for bad types |
| POST /api/admin/toggle-user | Crashed on missing/non-string `user_id`; `None['is_active']` crash when DB returns no row | Added type check + null guard |
| POST /api/admin/company/roles (create) | `.strip()` on non-string `name` (e.g. `123`) raised `AttributeError` | Validate `isinstance(name, str)` before strip |
| PUT /api/admin/company/roles/id (update) | Same `.strip()` crash on non-string name | Same fix |
| POST /api/admin/org/business-units + PUT | Same `.strip()` crash | Same fix |
| POST /api/admin/org/locations + PUT | Same `.strip()` crash | Same fix |
| DELETE /api/admin/org/business-units/id | `None['c']` crash when count query returns no row | Added null guard with `row['c'] if row else 0` |
| DELETE /api/admin/org/locations/id | Same `None['c']` crash | Same fix |

<!--
  ARCHIVIST'S NOTE (8 Aug 2026): exported verbatim. Be aware the hard-coded test counts above
  (4,494 total, and the per-file breakdown) were a point-in-time snapshot and were already stale
  when exported. Run `python -m pytest -q` for real numbers. Kept unaltered as the historical record.
-->
