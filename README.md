# HR Portal — Employee Management System

A multi-tenant, role-based HR management web application built with **Flask** and **PostgreSQL**. Supports employee registration, org hierarchy, skills management, vacation workflows, company branding, and individual theming.

---

## Project Links

| Resource | URL |
|----------|-----|
| **GitHub Repository** | https://github.com/roysamiracc1-tech/employeemanagement |

### Documentation

All business, technical, and project-management documentation lives in this repository as markdown.
**Jira and Confluence were retired on 8 August 2026** — see
[`docs/project-management/README.md`](docs/project-management/README.md) for how documentation and the
backlog are maintained now.

| Document | Path |
|----------|------|
| Business documentation | [`docs/BUSINESS_DOCUMENTATION.md`](docs/BUSINESS_DOCUMENTATION.md) |
| Business overview, features & access rights | [`docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`](docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md) |
| Technical documentation | [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md) |
| Product backlog (epics & user stories) | [`docs/project-management/BACKLOG.md`](docs/project-management/BACKLOG.md) |
| Product roadmap | [`docs/product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](docs/product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md) |
| Architecture review | [`docs/ARCHITECTURE_REVIEW.md`](docs/ARCHITECTURE_REVIEW.md) |
| Confluence archive (frozen) | [`docs/archive/confluence-export/`](docs/archive/confluence-export/) |

---

## Product & Engineering Team — Governance

Work on the HR Portal is run by **two connected AI-persona orgs** — a **Product org** and an **Engineering
org** — defined under [`docs/product-team/`](docs/product-team/). The **Senior Product Manager (SPM)** and the
**Senior Architect** are peer leads: product owns *what/why/priority*, engineering owns *how/feasibility*, and
a release is gated **jointly** on the Architect's technical-readiness verdict and DevOps's production-readiness
evidence.

**Chain of responsibility:**

```
Senior Product Manager (SPM)  ◄──peer leads · joint gate──►  Senior Architect
   ├─ Business Analyst          → gaps, requirements, traceability      ├─ Senior Software Engineer → hard/cross-cutting features, review
   ├─ UX / Product Designer     → journeys, design specs, a11y          ├─ Mid-Level Engineer       → well-scoped features, escalate early
   ├─ UAT Lead                  → validation, test cases, sign-off      └─ Senior DevOps Engineer   → CI/CD, infra, observability, release
   ├─ Delivery / Release Mgr    → roadmap, readiness, release gate
   └─ Product Strategist        → opportunities, prioritisation, North Star
```

| File | Purpose |
|------|---------|
| [`00_README.md`](docs/product-team/00_README.md) | How the two orgs work + how each role maps to this repo's docs |
| [`01_TEAM_CHARTER.md`](docs/product-team/01_TEAM_CHARTER.md) | Shared backbone (load with every role, both orgs) |
| [`02`–`07`](docs/product-team/) | Product org — SPM + five specialists |
| [`08_ENGINEERING_CHARTER.md`](docs/product-team/08_ENGINEERING_CHARTER.md) · [`09`–`12`](docs/product-team/) | Engineering backbone + Architect, Senior/Mid engineers, DevOps |
| [`deliverables/`](docs/product-team/deliverables/) | **Produced for this project** — SPM kickoff, product roadmap (goals→epics→stories), and the Architect's knowledge-transfer + technical task breakdown |

Both orgs read the existing `docs/` (business, technical, Jira backlog, architecture review) as source
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
│   ├── BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md
│   ├── ARCHITECTURE_REVIEW.md
│   ├── project-management/       # backlog + how docs are maintained
│   ├── product-team/             # product & engineering persona orgs
│   └── archive/confluence-export/  # frozen Confluence snapshots
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

## Backlog — Foundational Epics

The first 10 epics (52 user stories) that built the portal. The full backlog — all 34 epics
including the in-flight architecture-hardening work — is in
[`docs/project-management/BACKLOG.md`](docs/project-management/BACKLOG.md).

`KAN-###` are local story IDs, not links. They came from a Jira project that was retired on
8 August 2026.

| Epic | ID | Stories |
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
