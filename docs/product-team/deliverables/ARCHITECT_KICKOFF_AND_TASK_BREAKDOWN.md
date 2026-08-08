# Architect Onboarding, Knowledge Transfer & Technical Task Breakdown — HR Portal — 2026-08-08

> Produced by the **Senior Architect** (`09_SENIOR_ARCHITECT.md`) on joining, after reading the technical docs,
> the architecture review, `CLAUDE.md`, and the actual `app/` + `database/` source. This is (1) the **knowledge
> transfer** to the engineering team (Senior SWE, Mid-level, DevOps), (2) the **ADRs I am locking first**, and
> (3) the **user stories subdivided into technical tasks with an owner per task**.
>
> **Peer interface:** this consumes the SPM's `deliverables/SPM_KICKOFF.md` and
> `deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`. Product owns *what/why/priority*; I own *how*. My
> technical-readiness verdict (§6) feeds the joint gate. Evidence is cited as `file:line` or finding `Fn` /
> story `KAN-*` / `EP*`. Where I lack evidence I mark it **Assumption/Unknown**, not fact.
>
> **Owner legend:** **ARCH** Senior Architect · **SNR** Senior Software Engineer · **MID** Mid-Level Engineer ·
> **DEVOPS** Senior DevOps Engineer. Every task obeys `CLAUDE.md` and the Engineering Charter DoD (§4).

---

## 0. Onboarding note to the engineering team — read before writing any code

Team — before your first PR, read these, in order:

1. `../../CLAUDE.md` — **the invariants. Non-negotiable.** Feature-access model, company scoping, org-change rules, and the regression flow-test discipline. Violating these is a rejected PR, full stop.
2. `../TECHNICAL_DOCUMENTATION.md` — the real architecture, data model (46 tables), APIs, the vacation engine (§6), org-change engine (§22), two-tier admin (§12).
3. `../ARCHITECTURE_REVIEW.md` — the audit. Findings **F1–F31** with `file:line`. This is our debt map; most tasks below trace to an `Fn`.
4. The module you're touching under `../../app/`, plus its tests under `../../tests/`.

**Do not trust the Engineering Charter §2 stack defaults** (FastAPI/React/TypeScript/Spring). This project is
**not** that. §2 of the charter itself says *"confirm the actual stack before assuming"* — I have, and the real
one is below. Build to what exists; don't smuggle in a framework nobody agreed to.

---

## 1. Scope reviewed

| Input | Status | Notes |
|---|---|---|
| `CLAUDE.md`, `README.md` | Read | Invariants + bootstrap + Jira map. |
| `docs/TECHNICAL_DOCUMENTATION.md` | Read | 22 sections, schema, APIs, engines. |
| `docs/ARCHITECTURE_REVIEW.md` | Read | F1–F31 (this review was itself produced by an architect-reviewer agent — I am building on it, not redoing it). |
| `docs/project-management/BACKLOG.md` | Read | EP28–34 hardening backlog (KAN-148…182). |
| `app/` source | Read | `__init__.py`, `db.py`, `config.py`, `auth.py`, `helpers.py`, 15 `routes/`, 9 `services/`. |
| `database/`, `requirements.txt`, `.github/workflows/` | Read | Schema baseline, deps, CI. |
| SPM deliverables | Read | Kickoff + roadmap; I adopt their Phase-0 gate as my first sprint. |
| Live prod environment / infra | **Unknown** | No deploy target evidenced; login says *"Demo environment"*. DevOps tasks below assume we are **standing up** staging/prod, not inheriting one. |

---

## 2. Knowledge transfer — the system as it actually is

### 2.1 Real stack (corrected — this is what you build to)
| Layer | Reality (evidence) | Charter default it replaces |
|---|---|---|
| Backend | **Flask ≥3.0**, `requirements.txt` | (not FastAPI, not Spring) |
| App wiring | **Module-level `app` built at import time — NO application factory** (`app/__init__.py:6`); `run.py` imports it. Confirms **F13**. | — |
| Routing | **15 route modules importing the shared `app` singleton and decorating it — zero Blueprints** (`app/routes/*.py`). Confirms **F14**. | — |
| Data access | **Raw SQL via `psycopg2` behind `app/db.py` (`query`/`execute`/`insert_returning`). NO ORM, NO SQLAlchemy.** | (not an ORM) |
| DB | **PostgreSQL** + `uuid-ossp`; authoritative `database/schema.sql` baseline (KAN-165 ✅). | matches |
| Service layer | Real and healthy: `app/services/` (`company_scope`, `analytics_service`, `org_change_service`, `email_service`, `import_service`, `notification_service`, `page_tracker`, `search_service`, `skills_intelligence_service`). | — |
| Frontend | **Jinja2 templates + vanilla JS, mostly inline; CSS custom properties. NO React, NO TypeScript, NO build toolchain / `package.json`.** Confirms F26. | (not React/TS) |
| Tests | **pytest + pytest-flask, ~4,511 tests, DB fully mocked** (`tests/conftest.py`). Confirms **F10**. | — |
| CI | **GitHub Actions** — test job (schema+seed) + fresh-DB boot drift check (KAN-169 ✅). | — |

**Implication for tasking:** "front-end task" here = a Jinja template + a `static/js/` ES module (vanilla),
**not** a React component. "Migrations" = versioned SQL under `database/migrations/` (Alembic can wrap them as
raw-SQL migrations without needing ORM models — see ADR-004). "Auth" plugs into the existing session model in
`app/auth.py`.

### 2.2 The invariants you cannot break (from `CLAUDE.md`)
- Feature access is driven **only** by `role_feature_access` (global) + `company_role_feature_access` (per-company). Route guards use `@require_feature_access('code')`; nav uses `has_feature_access('code')`. **Never** hardcode `@require_roles(...)` on a feature page. **Never** add per-feature sub-flags.
- Company roles are `company_id = <that company's UUID>` **only** — never `OR company_id IS NULL`.
- SYSTEM_ADMIN bypasses feature checks automatically.
- Org-change: sequential approval; an employee can never initiate their own move; company-scoped; use `app/services/org_change_service.py` — don't re-implement inline.
- **Nothing is "done" until `pytest` passes AND the regression flow test passes.**

### 2.3 Strengths to preserve (do not "refactor" these away)
Parameterised SQL everywhere (no injection — `app/db.py`), centralised + cached + company-scoped feature access
(`app/auth.py`), single-source company scope (`app/services/company_scope.py`), set-based core reads (no N+1 on
the hot `_EMP_SELECT`), broad test surface. **We harden the edges; we keep the core.**

### 2.4 Debt map (the audit, grouped for us)
Security P0: F1 auth · F2 CSRF · F3 XSS · F4 HTML/upload injection. Data/perf: F6/F23 indexes (✅ done),
F8 non-atomic writes, F22 N+1, F24 over-fetch. Reproducibility/testing: F9 schema (✅ baseline), F10 mocked DB,
F11 CI (✅), F12 coverage. Structure: F13 factory, F14 Blueprints, F15 unpinned deps, F29 helpers grab-bag,
F30 guard audit. Scale: F7 pool, F16 cache, F17 polling, F18 uploads, F19 threads. Frontend/a11y: F20, F21,
F26, F27, F28.

---

## 3. ADRs I am locking first (so engineers don't each invent an answer)

| ADR | Decision | Rationale | Affects |
|---|---|---|---|
| **ADR-001** | **Auth = OIDC via Authlib** (not a bespoke password store). Session model in `app/auth.py` stays; OIDC provides the verified factor. | Closes F1 *and* delivers the enterprise SSO the roadmap wants (EP40-S1); avoids building throwaway password auth for a demo. Keep a dev-only fallback behind an env flag for local testing. | KAN-148 |
| **ADR-002** | **CSRF = Flask-WTF `CSRFProtect`** + a `static/js/api.js` wrapper that injects the token on all JSON POST/PUT/DELETE. | Standard, minimal, matches KAN-149 acceptance; one client choke-point for the token. | KAN-149 |
| **ADR-003** | **Output escaping = one shared `static/js/dom.js`** exporting `escapeHtml` + a safe `` html`` `` tag; every `innerHTML` builder routes through it. Ships the F26 module extraction and kills F3 at the source. | Makes escaping the *default path* so new code can't reintroduce XSS (KAN-173). | KAN-150/173, F26 |
| **ADR-004** | **Migrations = Alembic in raw-SQL mode** (no ORM models); fold existing `database/migrations/02–07` under it; keep `schema.sql` as the generated baseline. | Version tracking + ordering without adopting SQLAlchemy (we have no ORM). | KAN-166 |
| **ADR-005** | **Adopt `create_app(config)` factory** (F13) — but as an **enabling refactor sequenced after the P0 security items**, not before. Blueprints (F14) deferred to a later phase. | The factory unblocks test/staging/prod configs and real-DB tests; doing it first would churn every file during the security sprint. | KAN-178 |
| **ADR-006** | **Add a `transaction()` context manager in `app/db.py`** (single commit/rollback); wrap all composite writes. | Fixes F8 non-atomic writes without a broad rewrite. | KAN-155 |
| **ADR-007** | **Sanitisation = `bleach` allowlist** for company `header_html`/`footer_html`; drop `svg` from allowed uploads; serve uploads `Content-Disposition: attachment`. | Matches KAN-151; least-surprise, well-trodden. | KAN-151 |

Anything an engineer wants to do differently from an ADR: **escalate to me**, don't just diverge.

---

## 4. Technical task breakdown — user stories → tasks → owners

**Ground rules for every task:** small single-purpose PR · unit **and** (where it touches SQL) integration
tests · no real PII in tests · obey the `CLAUDE.md` invariants · reversible migration if schema changes ·
regression flow test green before "done". I (ARCH) review anything touching schema, auth, tenancy, or public
routes; SNR reviews MID PRs.

### Sprint 0 focus = the Phase-0 gate (BG1). These P0 security stories are the priority.

---

#### KAN-148 — Real authentication (OIDC) — **F1, P0** — lead: SNR · design: ARCH
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-148-1 | ARCH | ADR-001 finalised; pick OIDC lib (Authlib); define provider config contract (env-driven, per-deploy). | — |
| T-148-2 | SNR | Integrate Authlib OIDC login/callback in `app/routes/auth.py`; exchange verified identity → existing session (`app/auth.py`). Remove email-only session minting (`auth.py:82-115`). | integration: valid code → session; bad/expired code → no session |
| T-148-3 | SNR | Dev-only fallback login behind `APP_ENV=development` flag so local/tests keep working; **prod refuses it**. | test: fallback disabled when `APP_ENV=production` |
| T-148-4 | MID | `templates/login.html`: remove rendering of real admin/HR emails to anonymous users (F1 enumeration); replace with "Sign in with SSO". | UI/regression assert no seeded emails in anonymous HTML |
| T-148-5 | SNR | Update the ~existing auth tests + `tests/conftest.py` login helper to the new flow. | full suite green |
| T-148-6 | DEVOPS | OIDC client secret via secrets manager/env (never in code); document provider setup in runbook. | secret-scan clean |

#### KAN-149 — CSRF protection — **F2, P0** — lead: SNR · review: ARCH
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-149-1 | SNR | Add `Flask-WTF` to `requirements.txt` (pinned); enable `CSRFProtect` in app setup (`app/__init__.py`). | app boots; token present |
| T-149-2 | MID | Add hidden CSRF token to every server-rendered `<form>` (templates with POST). | per-form render test |
| T-149-3 | SNR | Create `static/js/api.js` (`postJSON`/`getJSON`) that injects the CSRF header on all unsafe fetches; migrate inline `fetch` POSTs (~44 endpoints) to it. | reject without token; accept with |
| T-149-4 | MID | Fix `tests/conftest.py:19` — `WTF_CSRF_ENABLED=False` is currently a no-op (Flask-WTF wasn't a dep); make it real; add accept/reject cases. | 44-route smoke: unsafe verbs require token |

#### KAN-150 + KAN-173 — Output escaping (finish it) — **F3, P0** — lead: SNR (ADR-003)
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-150-1 | SNR | Create `static/js/dom.js` — `escapeHtml` + safe `` html`` `` tag + `el()` helper (F26 Stage 1). | Vitest-style unit once JS tests exist (KAN-176); interim: manual |
| T-150-2 | SNR | Route the already-covered screens' `escH()` through `dom.js` (directory, org-tree, team, my-team) to dedupe. | regression: `<img onerror>` name renders inert |
| T-150-3 | MID | Cover the **remaining** screens (admin panel, profile, search, register) still building `innerHTML` unescaped. | per-screen XSS-payload render test |
| T-150-4 | ARCH | Add a review-checklist note / lightweight grep check discouraging raw `innerHTML` with interpolation. | CI grep warns on new raw `innerHTML +` |

#### KAN-151 — Company HTML + upload sanitisation — **F4, P0** — lead: SNR (ADR-007)
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-151-1 | SNR | Sanitise `header_html`/`footer_html` on **write** with a `bleach` allowlist (`app/routes/company.py:86-87,186-187`); or drop `| safe` at render (`templates/base.html:255,344`). | stored `<script>`/`onerror` stripped |
| T-151-2 | MID | Drop `svg` from allowed logo uploads (or rasterize); add content-type + magic-byte check (`app/helpers.py:7,18-28`). | reject `.svg`/spoofed type |
| T-151-3 | MID | Serve `/static/uploads/logos` with `Content-Disposition: attachment`. | header asserted |
| T-151-4 | SNR | Set `MAX_CONTENT_LENGTH` sanity re-check with upload cap (pairs with KAN-152 ✅). | oversize upload rejected |

#### KAN-153 — Required DB config, no personal defaults — **F31, P2** — lead: MID
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-153-1 | MID | `app/config.py:15-21`: require `PGUSER`/`PGDATABASE`; remove `'samirroy'` default; clear startup error if unset. | boot fails fast without env |

---

### Data-correctness (P1, run alongside security)

#### KAN-155 — Atomic composite writes — **F8** — lead: SNR (ADR-006)
| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-155-1 | SNR | Add `transaction()` context manager to `app/db.py` (single commit/rollback; no per-statement commit in `execute`). | rollback-on-error unit |
| T-155-2 | SNR | Wrap vacation-type create/edit (`vacation.py:87-93,142-150`) and org-change apply (`org_change_service.py:56-68,162-163`). | mid-loop failure leaves **no** partial rows (integration) |
| T-155-3 | MID | Ensure read paths don't sit idle-in-transaction (autocommit for reads or commit/rollback in `query`). | connection-state test |

#### KAN-156 — Kill N+1s — **F22** — lead: MID · review: SNR
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-156-1 | MID | Analytics overview: one `GROUP BY route` instead of per-feature COUNT (`analytics_service.py:76-90`). | row-count parity vs old |
| T-156-2 | MID | Vacation page: used-days for all types in one `GROUP BY` (`vacation.py:189-192`). | parity |
| T-156-3 | MID | Team-pending: replace correlated subselect with a windowed/join query (`vacation.py:379-385`). | parity |

---

### Reproducibility, testing & CI (P1) — enables everything above to be trusted

#### KAN-168 — Real-DB integration tier — **F10** — lead: DEVOPS + SNR
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-168-1 | DEVOPS | CI service-container Postgres (or testcontainers); apply `schema.sql`+`seed_rbac.sql`; expose a real-DB pytest marker. | tier runs in CI |
| T-168-2 | SNR | Port the org-change decide→apply flow to an integration test asserting **row state** (not SQL-string/`side_effect` order — F10 #4 / KAN-171). | final DB state asserted |
| T-168-3 | MID | Add real-DB tests for the vacation round-trip (submit→approve→reject) asserting persisted rows + audit. | green on real schema |

#### KAN-166 / KAN-167 — Migrations tool + single seed owner — **F9** — lead: SNR (ADR-004)
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-166-1 | SNR | Adopt Alembic (raw-SQL mode); fold `migrations/02–06` in; `alembic upgrade head` on fresh DB == full schema. | fresh-DB CI job passes via Alembic |
| T-167-1 | SNR | One owner for `portal_features`/`role_feature_access` seed — `setup_db.py` vs `alter_table.sql` must not diverge (F9); the other references it. | fresh bootstrap unambiguous |

#### KAN-170 — Coverage floor — **F12** — lead: DEVOPS
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-170-1 | DEVOPS | Add `pytest-cov` (pinned); `--cov=app --cov-report=term-missing`; fail CI under agreed floor; surface `email_service`/`page_tracker`/`skills_intelligence_service` gaps. | CI fails below floor |

#### KAN-180 — Pin dependencies — **F15** — lead: DEVOPS
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-180-1 | DEVOPS | Pin exact versions + lockfile (`pip-compile`/`uv`); CI installs from lock; add dependency **security scan** (charter §7 — a broken scan is release-blocking). | reproducible build; scan gate |

---

### Enabling refactor (P2, sequenced AFTER the P0 sprint — ADR-005)

#### KAN-178 — Application factory — **F13** — lead: SNR · design: ARCH
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-178-1 | ARCH | Design `create_app(config)`: config, teardown, context processor, route registration; note Blueprints (F14) as a **later** epic. | ADR-005 |
| T-178-2 | SNR | Implement `create_app`; `run.py` + tests build via it; multiple app instances coexist (unlocks per-config real-DB tests). | app boots test/prod config; suite green |

---

### First new-epic slice (Phase-1 preview) — proves the pattern for the roadmap's growth work

#### EP35-S2 — Bulk import dry-run — lead: SNR (builds on existing `app/services/import_service.py`, `app/routes/imports.py`)
| Task | Owner | Detail | Tests |
|---|---|---|---|
| T-35S2-1 | ARCH | Design the import contract: upload → column-map → **dry-run diff** (create/update/error rows) → commit; atomic per batch (reuses ADR-006 `transaction()`). | ADR + acceptance with BA |
| T-35S2-2 | SNR | Implement dry-run (validate + diff, no writes) in `import_service.py`; company-scoped; duplicate detection by employee #/email. | integration: dirty CSV → correct diff, zero writes |
| T-35S2-3 | MID | Commit path writes atomically; row-level error report; UI states (loading/partial/error) in the imports template. | partial-failure rolls back batch |
| T-35S2-4 | DEVOPS | Ensure import runs don't block a web worker (bounded — ties F19); log with correlation id. | load/timeout check |

*(Growth epics EP36–EP41 are broken down in later sprints once BG1 closes — not front-loaded, per MVP discipline.)*

---

## 5. Registers I now own

### 5.1 Technical Debt Register (seeded from the audit)
| ID | Debt | Source | Planned in | Sev |
|---|---|---|---|---|
| TD-1 | No app factory / import-time wiring | F13 | KAN-178 (ADR-005) | P1 |
| TD-2 | Zero Blueprints; route→route imports | F14 | later epic (post-P0) | P1 |
| TD-3 | `helpers.py` low-cohesion grab-bag | F29 | later (EP34 KAN-181) | P2 |
| TD-4 | Guard-decorator inconsistency (`require_roles` vs `require_feature_access`) | F30 | audit KAN-182 (do **not** blindly convert — CLAUDE.md) | P2 |
| TD-5 | Inline JS duplication / no `static/js/` | F26 | ADR-003 dom.js starts the paydown | P2 |
| TD-6 | 1,234 inline styles, non-semantic clickables | F28 | later (KAN-177) | P2 |

### 5.2 Technical Risk Register
| ID | Risk | Prob | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| TR-1 | OIDC integration touches the session/auth core → regressions across all guarded routes | Med | High | Feature-flag; keep dev fallback; heavy integration tests (T-148-5); ARCH-reviewed | SNR |
| TR-2 | CSRF rollout breaks the ~44 inline `fetch` POSTs if any is missed | Med | Med | Route all through `api.js`; 44-route smoke test (T-149-4) | SNR |
| TR-3 | Alembic adoption diverges from the `schema.sql` baseline | Low | High | `alembic upgrade head` == `schema.sql` asserted in CI (T-166-1) | SNR/DEVOPS |
| TR-4 | Real-DB tier flakiness slows CI | Med | Med | Ephemeral container per run; separate marker; parallelism cap | DEVOPS |
| TR-5 | No known staging/prod target → production-readiness unprovable | High | High | DEVOPS to stand up staging with parity + tested rollback before any GO | DEVOPS |

---

## 6. Technical-readiness verdict (feeds the joint gate)

**NO-GO for production — RAG 🔴 for the security dimension, 🟡 overall.** Open P0s F1–F4 (KAN-148/149/150+173/151)
are technical release-blockers; I will not certify technical readiness with any of them open (Architect
guardrail). Additionally, per **TR-5**, DevOps has **no evidenced staging/prod environment or tested rollback** —
production-readiness cannot be *proven* yet regardless of code.

**What flips my verdict to GO:** KAN-148/149/150+173/151 merged with tests (incl. the real-DB tier KAN-168 so
the SQL is actually verified) · dependency + secret scans green (KAN-180) · a staging environment at parity with
a **tested rollback** (DEVOPS) · UAT sign-off on the two flagship flows (product side).

---

## 7. Assignment summary (who owns what, Sprint 0)

- **ARCH (me):** ADR-001…007; design of auth (T-148-1), factory (T-178-1), import contract (T-35S2-1); review of every schema/auth/tenancy/route PR; the `innerHTML` review-gate (T-150-4); technical-readiness reporting to the SPM.
- **SNR (Senior SWE):** the hard/cross-cutting cores — OIDC (KAN-148), CSRF wrapper + `api.js` (KAN-149), `dom.js` + escaping consolidation (KAN-150/173), HTML sanitisation (KAN-151), `transaction()` + atomic writes (KAN-155), Alembic (KAN-166/167), real-DB org-change test (T-168-2), factory impl (T-178-2), import dry-run (T-35S2-2). Reviews all MID PRs.
- **MID (Mid-Level):** well-scoped, pattern-following work — login template de-enumeration (T-148-4), CSRF form tokens + test fix (T-149-2/4), remaining-screen escaping (T-150-3), upload checks + attachment header (T-151-2/3), config hardening (KAN-153), N+1 rewrites (KAN-156), vacation real-DB tests (T-168-3), import commit path/UI (T-35S2-3). Escalates ambiguity early.
- **DEVOPS:** real-DB CI tier (KAN-168-1), coverage floor (KAN-170), dependency pin + security scan (KAN-180), OIDC secret handling (T-148-6), **stand up staging/prod with parity + tested rollback + runbook** (TR-5), observability for new paths. Supplies production-readiness evidence to the Delivery Manager.

---

## 8. Open questions to the SPM / product (peer interface)

1. **OIDC provider?** (Which IdP for the first customer — Azure AD / Okta / Google?) Decides KAN-148 config. → SPM/product owner.
2. **Is there any target hosting environment** (cloud, container platform), or do we choose one? Blocks TR-5 and all production-readiness evidence. → product owner.
3. **Confirm Alembic (ADR-004) is acceptable** given no ORM — or keep hand-numbered SQL migrations? I recommend Alembic. → this is my call unless product objects; logged as ADR.
4. **Definition of Ready check:** EP35 (onboarding/import) needs BA acceptance criteria + data mapping before MID starts the commit path. → BA (via SPM).

*Everything above obeys `CLAUDE.md`. No task is "done" until `pytest` and the regression flow test pass, and no
security P0 is closed without a real-DB-backed test proving it.*
