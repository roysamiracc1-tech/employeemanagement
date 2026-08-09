# HR Portal — Architecture Review

> Produced by the **`architect-reviewer`** agent (`.claude/agents/architect-reviewer.md`) as a strictly
> read-only, evidence-backed audit across six dimensions: Architecture & Structure, Data Layer & SQL,
> Performance, Scalability, Security, Frontend & Modernization, and Testing & CI.
> All evidence is cited as `file:line`. No source files were modified during the review.

---

## Executive summary

The HR Portal is a well-organised Flask + PostgreSQL application with genuinely strong points: a centralised
company-scope module, a cached and correctly-scoped feature-access model that matches the `CLAUDE.md`
invariants, uniformly **parameterised SQL** (no injection found), set-based core reads that avoid N+1, and a
large (4,511) test suite. The biggest risks are not in the domain logic but around the edges: **the login
performs no credential check and there is no CSRF protection**, **client code injects unescaped data into
`innerHTML`** (stored XSS), the **schema cannot be rebuilt from the repo** (multiple sources of truth; the new
`org_change` tables live only in a migration), **every DB call in the test suite is mocked** so no SQL is
verified against a real database, and there is **no CI** — only a bypassable local pre-commit hook. Structural
debt (no app factory / Blueprints, a per-request DB connection with no pool, and heavily duplicated inline JS)
is real but lower-urgency. The top wins: lock down auth/CSRF/output-escaping, make the schema reproducible +
add real-DB CI, add a connection pool + the missing `employees(company_id)` index, and extract the shared
frontend JS to a small module layer (which also fixes the XSS at the source).

**Severity note:** several P0/P1 severities are *conditional on the production environment* (is `SECRET_KEY`
set? is Gunicorn used instead of `run.py`? is email-only login a deliberate demo shortcut?). Those are flagged
under **Needs measurement** and should be confirmed before scheduling.

---

## Progress (updated)

Delivered on branch `chore/arch-review-and-hardening` (PR #2), each verified + test-gated:

| Finding | Story | Status |
|---------|-------|--------|
| F3 (partial) | KAN-150 | 🟡 Output escaping via global `escH()` on directory, org-tree, team-vacation, my-team; remaining screens → KAN-173 |
| F5 | KAN-152 | ✅ Secure runtime defaults — `SECRET_KEY` prod fail-fast, `SESSION_COOKIE_*`, env-driven debug, `MAX_CONTENT_LENGTH` |
| F6 | KAN-154 | ✅ `employees(company_id, employment_status)` index (migration 07) |
| F23 | KAN-157 | ✅ `(company_id)` indexes on BU/loc/FU + `vacation_requests(vacation_type_id)` |
| F9 | KAN-165 | ✅ Authoritative `database/schema.sql` baseline + `seed_rbac.sql`; README bootstrap updated |
| F11 | KAN-169 | ✅ GitHub Actions CI — test job (schema+seed) + fresh-DB schema/boot drift check |
| F8 | KAN-155 | ✅ `transaction()` in `app/db.py` (ADR-006) — single commit/rollback; `execute()` no longer commits per statement inside a block; connections `autocommit=True` so reads never sit idle-in-transaction and a failed statement no longer poisons the request. Wrapped: vacation-type create/edit, org-change `save_workflow`/`create_request`/`apply_change`/`decide()` (incl. final apply + close-out, TD-7). Remaining non-atomic paths are **out of F8's named scope and now tracked separately** — employee registration (`admin.py:178-232`), role reassignment (`api_update_roles`), company-role/admin seeding, company create (`company.py:96-147`), CSV import apply (`import_service.py:123-175`) |

**Also surfaced by CI:** a chunk of the "unit" suite is really integration tests needing a live DB, and
`setup_db.py` can't bootstrap the canonical `schema.sql` (rolls back on `ON CONFLICT`) — captured as
**KAN-167** (single seeding owner) and **KAN-168** (real-DB integration tier). Remaining high-value items:
**KAN-148** (auth), **KAN-149** (CSRF), **KAN-151** (HTML/upload sanitisation), **KAN-159** (connection pool).

---

## Consolidated findings (deduplicated, ranked)

Severity: **P0** = correctness/security/scaling risk that will bite in production · **P1** = clear
structural/perf/process debt to schedule soon · **P2** = polish. Effort: S / M / L.

| # | Sev | Theme | Finding | Evidence | Recommendation | Effort |
|---|-----|-------|---------|----------|----------------|--------|
| F1 | P0 | Security | **Login performs no credential verification** — any active user's email grants a full session as that user; the login page enumerates real admin/HR emails to unauthenticated clients. | `app/routes/auth.py:82-115`, `:11-70` | Add a real auth factor (password hash / SSO-OIDC / signed magic-link with expiry); stop rendering real emails to anonymous visitors. | L |
| F2 | P0 | Security | **No CSRF protection** anywhere; Flask-WTF isn't even a dependency, so `WTF_CSRF_ENABLED=False` in tests is a no-op. ~44 state-changing endpoints exposed. | `requirements.txt`; `tests/conftest.py:19`; grep `methods=['POST'…]` | Add `CSRFProtect` (or double-submit token for JSON) and require it on all unsafe methods. | M |
| F3 | P0 | Security / Frontend | **Stored XSS via unescaped `innerHTML`.** User data (name, job title, skill, unit) is interpolated into `innerHTML` with no escaping; `directory.html` defines no `esc()` at all. ~20 templates build `innerHTML` without an escaper. | `templates/employees/directory.html` `buildRow`; `templates/org/tree.html:130-163`; also `vacation/team.html`, `my_team.html`, `admin/panel.html` | Route all dynamic `innerHTML` through a shared `escapeHtml`/safe-`html\`\`` helper, or use `textContent`. Fixed structurally by frontend module extraction (F26). | M |
| F4 | P0 | Security | **Stored HTML injection** — company `header_html`/`footer_html` stored verbatim and rendered with `| safe` to every employee; unvalidated SVG logo uploads served same-origin as active content. | render `templates/base.html:255,344`; write `app/routes/company.py:86-87,186-187`; `app/helpers.py:7,18-28` | Sanitize HTML on input (allowlist / bleach) or drop `| safe`; drop `svg` from allowed uploads or rasterize; serve uploads with `Content-Disposition: attachment`. | M |
| F5 | P1 | Security | **`SECRET_KEY` has a hardcoded fallback** (`'hr-portal-dev-secret-2024'`); session cookies lack `Secure`/`SameSite` flags; `run.py` runs `debug=True` on `0.0.0.0`; no `MAX_CONTENT_LENGTH`. | `app/config.py:4`; no `SESSION_COOKIE_*`; `run.py:4` | Fail-fast if `SECRET_KEY` unset in prod; set `SESSION_COOKIE_SECURE/SAMESITE/HTTPONLY`; drive `debug` from env (default off); set an upload size cap. | S |
| F6 | P1 | Data / Perf | **No index on `employees.company_id`** — the single most-filtered column — so every dashboard/directory/analytics query seq-scans `employees`. | live `pg_indexes`; `helpers.py:133`, `dashboard.py:55-89`, `analytics_service.py:28-454` | `CREATE INDEX ON employees(company_id)`; prefer composite `(company_id, employment_status)` (supersedes the low-value `idx_employees_status`). | S |
| F7 | P1 | Scalability / Data | **No DB connection pool** — a fresh `psycopg2.connect()` (TCP+auth) per request and per background thread. | `app/db.py:11-20`; `app/services/page_tracker.py:47-55` | Introduce `ThreadedConnectionPool` (or PgBouncer) behind `get_db()`. | M |
| F8 | P1 | Data | **Non-atomic multi-statement writes** — `execute()` commits after each statement and routes write in per-row loops, so a mid-loop failure leaves partial data. No rollback on error → aborted-transaction cascades; read paths sit idle-in-transaction. | `app/db.py:29-33`; `vacation.py:87-93,142-150`; `org_change_service.py:56-68,162-163` | Add a `transaction()` context manager (single commit/rollback); wrap composite writes; `autocommit=True` for read paths or commit/rollback in `query`. | M |
| F9 | P1 | Data / Testing | **Schema cannot be rebuilt from the repo.** `schema_v2.sql` lacks core tables (`companies`, `employees.company_id`, `vacation_*`, `page_views`, `user_notifications`, …); the new `org_change_*` tables exist only in migration 06; `portal_features` DDL/seed is defined twice (`alter_table.sql` + `setup_db.py`). A fresh DB per the README enables `org_change` in nav but has no backing tables → 500s. | `database/schema_v2.sql` vs live `pg_tables`; `database/migrations/06_...sql`; `scripts/setup_db.py:42-60`, `:114`; `README.md:96` | Produce one authoritative schema (`pg_dump --schema-only` baseline or complete numbered migrations); pick a single owner for feature/role seeding; document a canonical bootstrap. | M |
| F10 | P1 | Testing | **No real-DB coverage — every DB call is mocked.** SQL is never executed against the real schema, so column/type/constraint errors pass green. | `tests/conftest.py:3`; `app/db.py` never exercised | Add an integration tier: pytest + disposable Postgres (testcontainers or CI service container) hitting real routes/services. | L |
| F11 | P1 | Testing / CI | **No CI pipeline.** The only gate is a machine-local, bypassable (`--no-verify`) pre-commit hook; no lint, no coverage, not shared with teammates. | `.github/workflows` absent; `.git/hooks/pre-commit` | GitHub Actions: lint + full pytest + build-fresh-DB-from-migrations + boot smoke test, as a required check. | M |
| F12 | P1 | Testing | **No coverage measurement** (`pytest-cov` not installed); several modules have zero direct tests (`email_service`, `page_tracker`, `skills_intelligence_service`). | `requirements.txt`; `pytest.ini:6` | Add `pytest-cov`, `--cov=app --cov-report=term-missing`, enforce a floor in CI. | S |
| F13 | P1 | Architecture | **No application factory** — a module-level `app` is built at import time; all wiring is an import side-effect; no `create_app(config)`. | `app/__init__.py:6-37`; `run.py:1` | Introduce `create_app(config)`; move registration into it. | M |
| F14 | P1 | Architecture | **Zero Blueprints** — 15 route modules import the shared `app` singleton and decorate it; registration is a hand-maintained import list; near-circular graph with route→route imports. | 15× `from app import app`; `app/__init__.py:31-33`; `app/routes/company.py:7` | Convert route modules to Blueprints registered in the factory; move shared route helpers into services. | L |
| F15 | P1 | Architecture | **Unbounded/unpinned dependencies** — all deps use `>=`, no lockfile. | `requirements.txt:1-7` | Pin exact versions + lockfile (`pip-compile`/`uv`). | S |
| F16 | P1 | Perf | **Feature-access join runs on every rendered request** (cached per-request in `g`, but never across requests despite near-static tables). | `app/auth.py:38-95,141-165` | Short-TTL process cache keyed by `(sorted(roles), company_id)`, invalidated on permission writes. | M |
| F17 | P1 | Perf / Scale | **Bell polling fans out 2 COUNT queries per user every 60s** on every open tab, active or idle. | `templates/base.html:406-408,554`; `vacation.py:506-516`; `notifications.py:138-147` | Visibility-gated polling or SSE/websocket push; combine into one endpoint returning both counts. | S |
| F18 | P1 | Scalability | **Local-disk upload storage** for logos breaks horizontal scaling (uploaded on A, 404 on B). | `static/uploads/logos`; `app/__init__.py:9` | Object storage (S3/GCS) + signed URLs / CDN. | M |
| F19 | P1 | Scalability | **Unbounded thread-per-task background work** (one daemon thread per email and per page-view); no queue/backpressure/retry; lost on restart. | `app/services/email_service.py:67`; `app/services/page_tracker.py:84-88` | Bounded worker pool / task queue (RQ/Celery or a single consumer + `queue.Queue`). | M |
| F20 | P1 | Frontend a11y | **Drag-and-drop org tree is mouse-only** — no keyboard path, no `tabindex`/ARIA (WCAG 2.1.1 failure on a core HR workflow). | `templates/org/tree.html:229-244` | Add a keyboard "Move…" affordance opening the same modal; `aria-grabbed` + live-region announcements. | M |
| F21 | P1 | Frontend a11y | **Modals lack dialog semantics** — no `role="dialog"`/`aria-modal`, no focus trap, no Esc-to-close; whole app has ~4 ARIA attributes. | `admin/panel.html:1043-1067`; modal markup across templates | Shared `modal.js` (focus trap, Esc, `role="dialog"`+`aria-modal`+labelledby). | M |
| F22 | P2 | Data | **N+1s:** analytics overview runs one COUNT per feature (9) over `page_views`; vacation page calls `used_days()` per type; team-pending runs a correlated `SUM` subselect per row. | `analytics_service.py:76-90`; `vacation.py:189-192`; `vacation.py:379-385` | Replace each with a single `GROUP BY`/windowed query. | S |
| F23 | P2 | Data | **Missing indexes** on `business_units/locations/functional_units(company_id)` and `vacation_requests(vacation_type_id)`. | live `pg_indexes`; `admin.py:238-240`; `vacation.py:64-67` | Add the four indexes. | S |
| F24 | P2 | Data / Perf | **Directory over-fetch** — loads all active company employees with per-row skill/cert `JSON_AGG` (5+ joins) and no pagination. | `helpers.py:42-138`; `employees.py:106` | Paginate; split a light list projection from the detail query; use psycopg2 type adapters instead of per-key `serialize`. | M |
| F25 | P2 | Perf / Scale | **Branding HTML carried in the signed session cookie** (`header_html`/`footer_html`), risking the ~4KB cookie limit and staleness. | `app/routes/auth.py:108-113`; `app/auth.py:150` | Keep only `company_id` in session; load branding server-side with a cached lookup (pairs with F16). | S |
| F26 | P1 | Frontend | **Pervasive JS duplication, all inline** — `avatarColor`/`initials`/`AVATAR_COLORS` copy-pasted in 7 templates; `esc()`/date formatters duplicated or missing; 29 inline `<script>` blocks; no `static/js/`. | `org/tree.html:109-119`, `admin/panel.html:1193-1215`, `vacation/team.html:79-83`, +others | Extract `static/js/` ES modules (`dom`, `avatar`, `format`, `api`, `modal`); load once. Kills F3 at the source and enables JS tests. | M |
| F27 | P2 | Frontend | **No JS tests, no bundling/minification/cache-busting** — `style.css` and inline JS served raw with no `?v=`, risking stale-asset bugs after deploys. | `base.html:8`; grep `v=` on static url_for = 0; no `package.json` | After F26, add Vitest units on the pure helpers; add a build hash / `?v=` (optional esbuild minify). | M |
| F28 | P2 | Frontend | **1,234 inline `style="…"`** attributes (247 in `admin/panel.html`) duplicating `style.css`; 31 non-semantic clickable elements; 210 inline `onclick`. | grep; `admin/panel.html` | Migrate high-traffic inline styles to CSS classes; prefer real `<button>`/`<a>` + `addEventListener`. | L |
| F29 | P2 | Architecture | **`helpers.py` is a low-cohesion grab-bag** (logo I/O, emp-number, 80-line SELECT, org-tree CTE, vacation rule engine, stats) imported by 7 call sites; business logic embedded in routes (`admin.py` = 30 routes / 82 DB calls). | `app/helpers.py`; `app/routes/admin.py` | Split into `services/{employees,org,vacation}` + `util/uploads`; treat routes as thin controllers; split `admin.py`. | L |
| F30 | P2 | Architecture / Security | **Guard-decorator inconsistency** — `require_feature_access` used in 3 modules, `require_roles` in 10. Audit each to confirm feature pages use feature access and document why admin/config gates stay role-based (per `CLAUDE.md`, do not blindly convert). | grep decorators | Audit + document; convert genuine feature pages only. | M |
| F31 | P2 | Config | **Personal defaults in config** — `PGUSER` defaults to `'samirroy'`; masks missing config. | `app/config.py:15-21` | Make DB env vars required; no personal defaults. | S |

---

## Proposed epics (map findings → backlog)

| Epic | Goal | Findings |
|------|------|----------|
| **EP28 — Security Hardening** | Close the auth/CSRF/XSS gaps and harden session/config/upload posture. | F1, F2, F3, F4, F5, F31 |
| **EP29 — Data Layer & Query Performance** | Add missing indexes, kill N+1s, make writes atomic, paginate heavy reads. | F6, F8, F22, F23, F24 |
| **EP30 — Scalability & Runtime** | Pooling, background-work queue, shared upload storage, push instead of polling, slim the session. | F7, F16, F17, F18, F19, F25 |
| **EP31 — Schema Source of Truth & Migrations** | One authoritative, reproducible schema + a real migration tool. | F9 |
| **EP32 — Testing & CI** | Real-DB integration tier, CI pipeline, coverage floor. | F10, F11, F12 |
| **EP33 — Frontend Modernization** | Extract shared JS modules (escape-by-default), fix accessibility, add JS tests + asset versioning. | F3, F20, F21, F26, F27, F28 |
| **EP34 — Architecture & Structure** | App factory + Blueprints, service extraction, dependency pinning, guard audit. | F13, F14, F15, F29, F30 |

*(F3 appears in both EP28 and EP33 — the vulnerability is security, the durable fix ships with the frontend
module extraction.)*

---

## Strengths (keep these)

- **SQL is uniformly parameterised** — no injectable concatenation of user input anywhere in `app/`; even
  dynamic `WHERE` fragments interpolate only fixed internal strings and bind all values (`app/db.py:23-33`).
- **Feature-access model is centralised, cached, and correctly company-scoped**, with automatic SYSTEM_ADMIN
  bypass, matching the `CLAUDE.md` invariants (`app/auth.py:38-113`); the historically-problematic
  Skills-Intelligence sub-flag is gone.
- **Company-scope resolution is a single source of truth** (`app/services/company_scope.py`).
- **Core reads avoid N+1** — `_EMP_SELECT` folds managers/org/skills/certs into one `LATERAL`+`JSON_AGG`
  query; analytics is set-based; recursive CTEs are depth-bounded and tenant-scoped (`helpers.py`, `org.py`).
- **Event/log tables are well-indexed** for the analytics predicates (`page_views`, `search_logs`).
- **Broad test surface** (4,511 tests) with dedicated access-control/company-scoping suites; a real (if local)
  pre-commit gate; genuine pure-unit tests for serialization.
- **Frontend is SPA-ready without being an SPA** — 20 templates already consume JSON via `fetch`, so
  modernization can proceed without backend changes; rich vanilla-JS UX at zero framework cost.

---

## Needs measurement (confirm before scheduling)

- **Production configuration** — Is `SECRET_KEY` actually set in prod? Is Gunicorn/uWSGI the real entrypoint
  (not `run.py` with `debug=True`)? Is traffic HTTPS-only behind a proxy setting Secure cookies? These decide
  whether F5 (and parts of F1) are P1 or live P0.
- **Login trust model** — Is email-only login (F1) a deliberate demo shortcut or the production mechanism?
  This reframes several severities.
- **Index impact** — `EXPLAIN (ANALYZE, BUFFERS)` the directory/dashboard queries before/after
  `idx_employees_company` (F6); confirm the polling queries (F17) are index-only.
- **Connection & thread pressure** — measure `pg_stat_activity` short-lived-connection rate and peak daemon
  threads under concurrent load / slow SMTP to size the pool and the worker queue (F7, F19).
- **Real coverage** — run `pytest --cov=app --cov-report=term-missing` for a baseline (F12).
- **Cookie size** — measure real `header_html`/`footer_html` payloads vs the 4KB cookie limit (F25).
- **Log-table growth** — `page_views`/`search_logs` scan cost as they grow; consider retention/partitioning.

---

## Frontend modernization — staged path (from the frontend review)

Evolution, not rewrite. A framework migration would risk the 4,511-test UX contract for little user-facing gain.

- **Stage 1 (do this; highest payoff, lowest risk):** create `static/js/` as native ES modules — `dom.js`
  (`escapeHtml` + safe `html\`\`` tag → fixes F3 by making escaping the default), `avatar.js`, `format.js`,
  `api.js` (one `postJSON`/`getJSON` wrapper, a natural home for the future CSRF header from F2), `modal.js`
  (focus trap + Esc + dialog semantics → F21; add the keyboard "Move" affordance → F20). Then add a few
  Vitest units on the now-pure helpers (first testable client logic). Mostly mechanical; each extraction
  ships independently and leaves Jinja untouched.
- **Stage 2 (optional):** a tiny render-component convention (`renderEmployeeRow`, `renderOrgCard`) on top of
  Stage 1 for the 2–3 heaviest screens — no framework, no virtual DOM.
- **Stage 3 (deferred; only on a concrete trigger):** a single embedded island (Preact/Vue, no router)
  behind the existing JSON APIs for one screen as a trial, before any broader commitment. Introduces
  `package.json`/node toolchain/build the team doesn't have today — justify only against a real wall.
