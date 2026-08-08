# HR Portal — Employee Management System

A multi-tenant, role-based HR management web application built with **Flask** and **PostgreSQL**. Supports employee registration, org hierarchy, skills management, vacation workflows, company branding, and individual theming.

---

## Project Links

| Resource | URL |
|----------|-----|
| **GitHub Repository** | https://github.com/roysamiracc1-tech/employeemanagement |
| **Jira Board** | https://roysamiracc1-1777144763345.atlassian.net/jira/software/projects/KAN/boards |
| **Confluence Space** | https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa |

### Confluence Documentation Pages

| Page | Link |
|------|------|
| Technical Documentation | https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/360451 |
| Business Documentation | https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/327683 |
| Jira Epics & User Stories | https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/393217 |

---

## Product Team & Governance

Product direction for the HR Portal is run by an **SPM-led product team** — a modular set of role
definitions under [`docs/product-team/`](docs/product-team/). Instead of ad-hoc decisions, work flows through
a **Senior Product Manager (SPM)** who tasks specialists (Business Analyst, UX/Product Designer, UAT Lead,
Delivery/Release Manager, Product Strategist), reviews their reports, reconciles conflicts, and makes the
phase-gate call.

**Chain of responsibility:**

```
Senior Product Manager (SPM) — orchestrate · review · reconcile · decide · gate
   ├─ Business Analyst         → gaps, requirements, traceability, conflicts
   ├─ UX / Product Designer    → journeys, design specs, accessibility
   ├─ UAT Lead                 → validation, test cases, sign-off
   ├─ Delivery / Release Mgr   → phased roadmap, readiness, release gate, risks
   └─ Product Strategist       → opportunities, prioritisation, North Star
```

| File | Purpose |
|------|---------|
| [`00_README.md`](docs/product-team/00_README.md) | How the team works + how each role maps to this repo's docs |
| [`01_TEAM_CHARTER.md`](docs/product-team/01_TEAM_CHARTER.md) | Shared backbone — vocabulary, scales, artifacts, report contract (load with every role) |
| [`02`–`07`](docs/product-team/) | The five specialist roles + the SPM |
| [`08_SPM_KICKOFF.md`](docs/product-team/08_SPM_KICKOFF.md) | **The SPM's onboarding, maturity read, phased roadmap, and current task assignments** |

The team reads the existing `docs/` (business, technical, Jira backlog, architecture review) as its source
material — see the "reads first" table in [`00_README.md`](docs/product-team/00_README.md). All engineering
changes still obey the invariants in [`CLAUDE.md`](CLAUDE.md).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 · Flask 3.x |
| Database | PostgreSQL 14+ (`uuid-ossp` extension required) |
| Frontend | Jinja2 · Vanilla JS · CSS custom properties |
| Auth | Server-side session (8-hour TTL) |

---

## Project Structure

```
employeemanagement/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # DB config, app settings
│   ├── db.py             # query / execute / insert_returning helpers
│   ├── auth.py           # login_required, require_roles, context processor
│   ├── helpers.py        # fetch_employees, vacation engine, org tree, save_logo
│   └── routes/
│       ├── auth.py       # login / logout
│       ├── dashboard.py  # dashboard + stats API
│       ├── employees.py  # directory, profile, my_team + APIs
│       ├── admin.py      # admin panel + register user + APIs
│       ├── org.py        # org tree + API
│       ├── company.py    # company view + admin company management
│       └── vacation.py   # all vacation routes
├── templates/
│   ├── base.html  login.html  dashboard.html
│   ├── admin/        # panel, register, companies, company_form, vacation_types
│   ├── employees/    # directory, profile, my_team
│   ├── org/          # tree
│   ├── company/      # view
│   └── vacation/     # employee, team
├── static/
│   ├── css/style.css
│   └── uploads/logos/
├── database/
│   ├── schema_v2.sql
│   ├── seed_data.sql
│   └── migrations/
├── docs/
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── BUSINESS_DOCUMENTATION.md
│   └── JIRA_EPICS_AND_STORIES.md
├── run.py
└── requirements.txt
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+ with `uuid-ossp` extension

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up the database

`database/schema.sql` is the **authoritative, complete schema** (a `pg_dump --schema-only`
baseline of all 46 tables, indexes, functions and triggers — regenerate with
`pg_dump -d employee --schema-only --no-owner --no-privileges -f database/schema.sql`).
Build a fresh database from it, then seed roles/features:

```bash
psql -U postgres -c "CREATE DATABASE employee;"
psql -U postgres -d employee -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql -U postgres -d employee -f database/schema.sql   # full structure (canonical)
python scripts/setup_db.py                             # seed roles, portal features, demo data
```

> `database/schema_v2.sql` and the numbered files in `database/migrations/` are **historical**
> — the current structure is already captured in `database/schema.sql`, so a fresh database
> should not replay the migrations. Add new schema changes as a new numbered migration **and**
> regenerate `schema.sql`.

### 4. Configure environment

```bash
export APP_ENV=development          # 'production' enables secure cookies + requires SECRET_KEY, forces debug off
export SECRET_KEY=your-secret-key   # REQUIRED when APP_ENV=production (app fails fast if unset)
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=employee
export PGUSER=your-db-user
export PGPASSWORD=your-db-password
```

### 5. Run the server

```bash
python run.py
```

Open **http://localhost:8000**

### Production

```bash
export APP_ENV=production
export SECRET_KEY=<random-256-bit-string>
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

---

## Testing & CI

```bash
python -m pytest -q                        # ~4,500 tests (needs the seeded dev DB running)
python tests/ui/test_browser.py            # browser regression suite (live server on :8000)
python tests/ui/test_vacation_workflow.py  # vacation-workflow regression
```

**GitHub Actions** (`.github/workflows/ci.yml`) runs on every push/PR: a **test job** (builds Postgres from
`database/schema.sql` + `database/seed_rbac.sql`, runs pytest) and a **fresh-DB schema + app-boot job** that
catches schema drift. See `docs/TECHNICAL_DOCUMENTATION.md` §11 and the improvement backlog in
`docs/ARCHITECTURE_REVIEW.md`.

---

## Key Features

- **8 RBAC roles** — SYSTEM_ADMIN, HR_ADMIN, Managers, Employee
- **Employee registry** — 6-step guided registration with auto-generated employee numbers
- **Org hierarchy** — recursive tree view with expand/collapse, up to 10 levels deep
- **Skills management** — self-assessment with 4 proficiency levels; manager validation
- **Certifications** — add, edit, remove with issuer, dates, and credential URL
- **Vacation system** — company-defined types, location scoping, eligibility rules (gender, tenure), full approve/reject workflow
- **Company branding** — logo upload, theme colour, HTML header/footer per company
- **Dark mode** — individual light/dark preference saved per user
- **Work anniversary badges** — animated indicators with urgency levels

---

## Jira Project — KAN

10 Epics · 52 User Stories — all tracked at:
https://roysamiracc1-1777144763345.atlassian.net/jira/software/projects/KAN/boards

| Epic | Key | Stories |
|------|-----|---------|
| Authentication & Session Management | KAN-2 | KAN-12 to KAN-15 |
| Role-Based Access Control | KAN-3 | KAN-16 to KAN-19 |
| Employee Registry & Directory | KAN-4 | KAN-20 to KAN-24 |
| Employee Profile & Self-Service | KAN-5 | KAN-25 to KAN-31 |
| Organisational Structure | KAN-6 | KAN-32 to KAN-36 |
| Manager Self-Service | KAN-7 | KAN-37 to KAN-38 |
| Vacation & Leave Management | KAN-8 | KAN-39 to KAN-51 |
| Company Branding & Theming | KAN-9 | KAN-52 to KAN-58 |
| Dashboard & Real-Time Metrics | KAN-10 | KAN-59 to KAN-62 |
| Work Anniversary Recognition | KAN-11 | KAN-63 to KAN-64 |
