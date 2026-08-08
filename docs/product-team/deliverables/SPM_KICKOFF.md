# SPM Onboarding & First Tasking — HR Portal — 2026-08-08

> Produced by the **Senior Product Manager** (`02_SENIOR_PRODUCT_MANAGER.md`) on joining the team, after
> reviewing the existing business and technical documentation in this repository. This is the SPM's intake
> read, maturity assessment, phased roadmap, and the **task assignment to each specialist**. It follows the
> Charter §6 reporting contract and the SPM "review the product progress" output shape.
>
> **Standing rule for the team:** everything below is evidence-led. Every claim cites a source already in the
> repo — `docs/BUSINESS_DOCUMENTATION.md`, `docs/TECHNICAL_DOCUMENTATION.md`, `docs/ARCHITECTURE_REVIEW.md`
> (findings `F1`–`F31`), `docs/project-management/BACKLOG.md` (epics `EP1`–`EP34`, stories `KAN-*`), and
> `CLAUDE.md`. Where evidence is missing it is labelled **Assumption** or **Unknown**, not asserted.

---

## 0. Onboarding note — "go read the existing docs first"

I'm new to this team, and so is my group of specialists. Before anyone proposes a single change, we read what
already exists. This product is **not** a blank page — it is a working, well-tested multi-tenant HR portal with
an unusually thorough paper trail. Our job is to judge it, not to re-imagine it.

**Required reading before your first report (everyone):**
1. `README.md` — what the product is, how to run it, the Jira map.
2. `docs/BUSINESS_DOCUMENTATION.md` — purpose, roles, the real business processes, retention/privacy, metrics, integration gaps.
3. `docs/TECHNICAL_DOCUMENTATION.md` — architecture, data model, APIs, security, the vacation engine, org-change workflow.
4. `docs/project-management/BACKLOG.md` — 27 delivered epics + the EP28–34 hardening backlog with per-story acceptance criteria and current status.
5. `docs/ARCHITECTURE_REVIEW.md` — the read-only audit; findings `F1`–`F31`, strengths, and the "Needs measurement" list.
6. `CLAUDE.md` — the **non-negotiable engineering invariants** (feature-access model, company scoping, org-change rules, the regression flow-test discipline). These are guardrails, not suggestions.

Each specialist's role file (`03`–`07`) tells you what to *produce*. The table in `00_README.md` tells you what
to *read first*. Report back to me in the Charter §6 format. I will challenge anything unevidenced.

---

## 1. Scope reviewed

| Input | Status | Notes |
|---|---|---|
| `README.md` | Read | Product overview, tech stack, bootstrap, Jira epic map (KAN). |
| `docs/BUSINESS_DOCUMENTATION.md` | Read | Purpose, 9 roles, business processes (onboarding, vacation, org-change), retention/privacy, metrics, integration points. |
| `docs/TECHNICAL_DOCUMENTATION.md` | Read | 22 sections incl. schema (46 tables), feature-permission matrix, two-tier admin, org-change engine, analytics. |
| `docs/project-management/BACKLOG.md` | Read | EP1–EP27 (✅ Done), EP28–EP34 (hardening; mixed 🟡/⬜). |
| `docs/ARCHITECTURE_REVIEW.md` | Read | Six-dimension audit, findings F1–F31, ranked, with `file:line` evidence. |
| `CLAUDE.md` | Read | Engineering invariants + regression flow-test protocol. |
| **The running build** | **Not yet exercised by this team** | App boots on `localhost:8000`; a hands-on UAT pass has not been run *by us*. Flagged as an entry task for UAT. |
| **Production configuration** | **Unknown** | Whether this is deployed anywhere, with what config, is not evidenced. Drives several severities (see §7). |
| **Real customers / commercial intent** | **Unknown** | No customer, contract, or go-live date is documented. Treated as **Assumption: pre-first-customer / demo-grade** until told otherwise. |

---

## 2. Summary verdict

**RAG: 🟡 Amber. Maturity: P3 Functional Product, moving toward P4/P5.**

This is a **feature-complete, heavily-tested functional product (4,511 tests, 27 delivered epics) with a
disciplined, already-scoped hardening backlog** — but it is **not yet production-ready and not yet
customer-ready**, and the gap is concentrated in a small number of high-severity security items, not in the
domain logic. Confidence: **High** (the architecture review is evidence-cited and the backlog is explicit).

The single most important thing I can say on day one: **the product's risk is at the edges, not the core.** The
domain model, company-scoping, feature-access system, and test breadth are genuine strengths
(`ARCHITECTURE_REVIEW.md` "Strengths"). What blocks a real deployment is **authentication (F1), CSRF (F2),
output-escaping/HTML-injection (F3/F4)** — and the honest answer to "is this production-ready?" is *no, and we
know exactly why.*

---

## 3. Current product state & maturity (with evidence)

**What exists and works (Known):**
- **Multi-tenant HR portal** — employees, org hierarchy (recursive tree to 10 levels), skills/certifications, vacation workflow, company branding, dashboards, notifications, analytics, and a sequential multi-level **position-change (org-change) approval engine**. Evidence: `BUSINESS_DOCUMENTATION.md` §3; `TECHNICAL_DOCUMENTATION.md` §6–§22; `JIRA` EP1–EP27 all ✅.
- **Correct, centralised access control** — feature access driven by `role_feature_access` / `company_role_feature_access`, cached, company-scoped, with automatic SYSTEM_ADMIN bypass; the historically-problematic Skills-Intelligence sub-flag has been removed. Evidence: `ARCHITECTURE_REVIEW.md` "Strengths"; `CLAUDE.md`.
- **Uniformly parameterised SQL** — no injection found anywhere in `app/`. Evidence: `ARCHITECTURE_REVIEW.md` "Strengths".
- **Large automated test surface** — 4,511 pytest tests plus two headless browser regression suites (`tests/ui/`). Evidence: `README.md` Testing; `CLAUDE.md`.
- **Hardening already underway** — on branch `chore/arch-review-and-hardening` (PR #2): secure runtime defaults (KAN-152 ✅), hot-path indexes (KAN-154/157 ✅), authoritative `schema.sql` baseline (KAN-165 ✅), GitHub Actions CI (KAN-169 ✅), partial output-escaping (KAN-150 🟡).

**What is not yet true (Known gaps, from the review):**
- **No real authentication** — a session is minted from an email match alone; the login page enumerates real admin/HR emails to anonymous visitors (F1, KAN-148, ⬜).
- **No CSRF protection** on ~44 state-changing endpoints (F2, KAN-149, ⬜).
- **Stored XSS / HTML-injection** paths remain on the screens not yet covered by `escH()` (F3 remainder → KAN-173), and company `header_html`/`footer_html` + SVG uploads render as active content (F4, KAN-151, ⬜).
- **No real-DB test tier** — every DB call in the mocked suite is unverified against a real schema (F10, KAN-168, ⬜); CI now partly closes this.
- **Not horizontally scalable yet** — per-request DB connections (F7), local-disk uploads (F18), unbounded background threads (F19).

**Maturity placement:** **P3 → P4.** It is well past MVP in features, but "UAT-Ready" (P4) requires a validation
pass *this team* has not yet run, and "Production-Ready" (P5) is blocked by F1–F4. I will not call it P5 until
those close and UAT signs off. (Charter §3, §9 rule 9.)

---

## 4. Reconciled priorities (P0–P4)

Priorities below reconcile the architecture review's severities with the business framing in the Jira backlog
("security items are Must-Have **pre-prod** — required before deployment, not live incidents"). This
reconciliation is itself a decision (see Decision Log, §9): **I am treating the app as pre-first-customer, so
F1–F4 are P0-for-the-production-gate, not P0-live-incidents.** If §7's production questions come back "yes,
it's exposed," these escalate to live P0 immediately.

| Priority | Items | Rationale |
|---|---|---|
| **P0 (gate-blocking)** | F1/KAN-148 auth · F2/KAN-149 CSRF · F3/KAN-150+173 output-escaping · F4/KAN-151 HTML/upload sanitisation | No product touching employee PII ships without real auth, CSRF, and output-escaping. These block the Production-Ready gate. |
| **P1 (before production)** | F10/KAN-168 real-DB test tier · F8/KAN-155 atomic writes · F31/KAN-153 required DB config · KAN-166 migration tool · KAN-170 coverage floor | Correctness & confidence: prove the SQL, make composite writes atomic, make the schema/CI trustworthy. |
| **P2 (production readiness)** | F7/KAN-159 connection pool · F16/KAN-160 feature-access cache · F22/KAN-156 N+1s · F24/KAN-158 directory pagination · F20/F21 a11y (KAN-174/175) | Reliability, performance, and accessibility for a real tenant at real size. |
| **P3 (scale / polish)** | F18/KAN-162 object storage · F19/KAN-163 bounded workers · F17/KAN-161 push-not-poll · F26/KAN-172 JS module extraction · EP34 factory/Blueprints | Needed for multi-instance scale and maintainability, not for a first pilot. |
| **P4 (strategic / future)** | Integrations (SSO/SCIM, HRIS import, calendar), and any AI/automation — **only** behind the Strategist's problem-first + compliance gate. | Deferred until the foundation is safe and a real problem is evidenced. |

---

## 5. Phased roadmap (summary)

Aligned to the Delivery role's phase model (`06_*`) and the existing EP28–34 mapping. **No calendar dates** —
targets are stated as exit criteria and dependencies, per the Delivery guardrail. Sequencing, not scheduling.

| Phase | Objective | In scope | Exit criteria | Depends on |
|---|---|---|---|---|
| **Phase 0 — Foundation & Hardening** *(in progress)* | Make the platform safe to expose and reproducible. | EP28 security (F1–F5, F31) · EP31 schema/migrations (F9, KAN-166/167) · EP32 CI + real-DB tier (F10–F12) | Real auth in place; CSRF on all unsafe routes; output-escaping + upload/HTML sanitisation complete; schema rebuildable from repo; real-DB integration tier green in CI; **one core flow (vacation round-trip) demonstrable end-to-end**. | Answers to §7 production questions. |
| **Phase 1 — MVP / GA-lite (first customer-ready slice)** | One tenant can adopt core HR + vacation for real, safely and accessibly. | Harden the two flagship flows (directory/self-service + vacation approval) to full compliance & WCAG 2.2 AA; EP29 correctness (KAN-155/156/158) | Passes **UAT for in-scope personas** (HR admin, manager, employee); ops runbook + admin/end-user docs exist; release gate green. | Phase 0 complete; UAT cohort + environment. |
| **Phase 2 — Production Readiness** | Reliable, performant, observable under a real tenant's load. | EP30 pooling/caching (F7, F16) · N+1 cleanup · a11y (F20/F21) · monitoring/alerting · backup/rollback verified | Production Readiness checklist green (Charter §4); load/`EXPLAIN` evidence for the "Needs measurement" items. | Phase 1 gate. |
| **Phase 3 — Customer Launch + Hypercare** | Get a pilot customer live and supported. | Onboarding, configuration, **data migration/import (CSV)**, provisioning, training, support, adoption analytics, hypercare | Customer Readiness checklist green; pilot live; hypercare window staffed. | Phase 2 gate; a real customer (Unknown today). |
| **Phase 4 — Expansion** | Deeper workflows, integrations, and *justified* AI. | SSO/SCIM, HRIS/calendar integrations, mobile depth, EP33/EP34 modernization, AI **only** behind compliance controls | Each item passes the Strategist's problem-first + EU AI Act / GDPR Art. 22 gate. | Phase 3; evidenced demand. |
| **Phase 5 — Scale & Optimisation** | Multi-tenant scale and cost. | Object storage (F18), bounded workers (F19), push notifications (F17), partitioning/retention on log tables | Multi-instance verified; performance/cost targets met. | Phase 4. |

---

## 6. Task assignments — who does what next

Each specialist loads `01_TEAM_CHARTER.md` + their own role file, reads the "reads first" set from
`00_README.md`, and returns a **Charter §6 report**. These are bounded first tasks, not the whole job.

### → Business Analyst (`03_BUSINESS_ANALYST.md`)
- **T-BA1** Build the **Product Understanding Summary** from `BUSINESS_DOCUMENTATION.md` + `TECHNICAL_DOCUMENTATION.md` (purpose, personas, workflows, capabilities, limitations, dependencies), each with evidence + confidence.
- **T-BA2** Stand up the **Traceability Matrix** for the two flagship flows (**vacation request round-trip** and **org-change approval**): Objective → Requirement → Story (KAN) → UX → Technical → Test → UAT. Flag every broken link.
- **T-BA3** Open the **Gap Register** with a compliance focus: **GDPR retention/erasure/DSAR** (note `BUSINESS_DOCUMENTATION.md` §4 keeps employee + vacation records indefinitely — is there a lawful basis and an erasure path?), audit-trail completeness, and any requirement with untestable acceptance criteria.
- **T-BA4** Start the **Conflict Log** — reconcile the architecture review's "pre-prod, not live" framing against the raw P0 severities; surface, do not silently resolve.
- *Deliver:* BA Report + those four registers. **Do not** invent requirements; label Known/Assumption/Unknown.

### → UX / Product Designer (`04_UX_PRODUCT_DESIGNER.md`)
- **T-UX1** Map the **vacation request → approval journey** and the **manager org-change** journey end-to-end (Discover → Confirm → Follow-up), calling out friction, and every required state (empty/loading/error/permission/partial/integration-failure).
- **T-UX2** Run the **accessibility audit** against WCAG 2.2 AA, starting from the two known failures: **mouse-only drag-and-drop org tree (F20)** and **modals with no dialog semantics/focus trap (F21)**. Confirm scope beyond those.
- **T-UX3** Review **trust/transparency** on anything touching personal data (who can see it, why) — this is an HR-UX gate, not decoration.
- *Deliver:* UX Report + journey maps + the a11y issue list tied to personas. Hand automation ideas to the Strategist.

### → UAT Lead (`05_UAT_LEAD.md`)
- **T-UAT1** Draft the **Phase-0/Phase-1 UAT plan**: personas (HR admin, solid-line manager, employee; IT/platform admin for tenancy), entry criteria, and a **stable UAT environment separate from dev** with **synthetic data only — never real PII**.
- **T-UAT2** Write **test cases for the flagship flows** mapped to BA's matrix (T-BA2): vacation happy/negative/edge, permissions & **tenant isolation**, audit trail, mobile behaviour for the employee/manager flows.
- **T-UAT3** Do a first **exploratory pass on the running build** and open the **Defect Log** — this team has not yet exercised the app by hand.
- *Deliver:* UAT plan + test cases + defect log. This is validation, not QA; do not sign off on hope.

### → Delivery / Release Manager (`06_DELIVERY_RELEASE_MANAGER.md`)
- **T-DEL1** Own the **phased roadmap** in §5 as a living artifact; expand Phase 0 and Phase 1 into per-item scope/exit-criteria/dependencies (no dates).
- **T-DEL2** Stand up the **Risk Register** and **Dependency Register** — seed them from the review's "Needs measurement" list (production config, login trust model, index/connection/coverage measurements) and the F1–F4 security risks.
- **T-DEL3** Draft the **Production Readiness** and **Customer Readiness** checklists (kept distinct, Charter §4); mark each line RAG with evidence.
- *Deliver:* Delivery Report + roadmap + both registers + both checklists + a first **Release Gate** table (expected verdict today: **NO-GO**, with F1–F4 as the blocking conditions).

### → Product Strategist (`07_PRODUCT_STRATEGIST.md`)
- **T-STR1** Propose a **North Star** grounded in this product — candidate: *"% of target HR workflows (vacation, org-change, profile self-service) completed by users without manual/off-system intervention"* — with the supporting adoption/efficiency/quality metrics beneath it.
- **T-STR2** Assess the **documented-but-unbuilt integrations** (`BUSINESS_DOCUMENTATION.md` §6: email ✅ built, calendar iCal, **CSV HRIS import**, **SSO/SAML/OIDC**) as Now/Next/Later — noting SSO/OIDC is also the clean answer to the auth gap (F1). Problem-first, RICE-ranked.
- **T-STR3** Scan for **automation** wins (bulk import, notification batching) that reduce Time + Errors + Ops cost. **Do not** propose AI features yet — if any surface, gate them behind the EU AI Act / GDPR Art. 22 checklist and flag for compliance.
- *Deliver:* Strategy Report + Now/Next/Later backlog + opportunity assessments. Guard the MVP.

---

## 7. Open questions / needs (blocking accurate severity)

These are the review's "Needs measurement" items. **Answers change the roadmap**, so I need them early —
routed to whoever can answer (owner in brackets):

1. **Is this deployed anywhere, or demo/local only?** [product owner] — decides whether F1–F4 are gate-blockers or *live* P0 incidents.
2. ~~**Is email-only login a deliberate demo shortcut or the intended mechanism?**~~ **ANSWERED (2026-08-08):** the login page prints *"Demo environment — no password required"* — it is a deliberate demo shortcut. The app is demo-grade today, so F1–F4 are **production-gate blockers, not live incidents**. Auth (KAN-148) should be delivered as **SSO/OIDC** — see `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` EP40-S1.
3. **Is there a target first customer / commercial timeline?** [product owner] — decides whether we drive to Phase 1 (GA-lite) now or keep hardening.
4. **Production config truth:** is `SECRET_KEY` set, is Gunicorn (not `run.py debug=True`) the entrypoint, is traffic HTTPS behind a proxy? [ops] — decides F5 live severity.
5. **Measurements:** `EXPLAIN (ANALYZE, BUFFERS)` on directory/dashboard pre/post index; `pg_stat_activity` connection rate under load; `pytest --cov` baseline; real `header_html` cookie size. [Delivery + dev] — sizes F6/F7/F12/F25.

Until #1–#3 are answered, the team proceeds on the stated **Assumption: pre-first-customer, hardening-first.**

---

## 8. Phase-gate recommendation

**Production-Ready gate: NO-GO** — open P0 security blockers F1 (auth), F2 (CSRF), F3 (remaining XSS),
F4 (HTML/upload injection). Per Charter §9 rule 9 and the SPM guardrails, I will not recommend GO with an open
P0. **Customer-Ready gate: NO-GO** — no onboarding/migration/training/hypercare assets exist yet, and UAT has
not been run by this team.

**Conditions to move the Production gate to GO:** close KAN-148/149/151 and finish KAN-150→173; land the
real-DB integration tier (KAN-168) so the SQL behind those changes is actually verified; UAT signs off the two
flagship flows for in-scope personas.

---

## 9. Decision Log (opened today)

| # | Decision | Context | Options considered | Rationale | Impact |
|---|---|---|---|---|---|
| D-001 | Treat the app as **pre-first-customer / hardening-first** until told otherwise. | No customer, deployment, or timeline is documented (§1, §7). | (a) assume live prod → all F1–F4 live P0; (b) assume demo → F1–F4 gate-blockers; (c) block until answered. | Picking (b) lets the team make progress on the right work now, while §7 Q1–Q3 are chased, without overstating incident severity. Re-evaluated the moment §7 is answered. | Sets P0 framing in §4; roadmap starts at Phase 0. |
| D-002 | **Phase 0 before any new features.** | Feature set is already broad (EP1–EP27 ✅); risk is in security/reproducibility, not missing features. | (a) build Phase-1 features now; (b) harden first. | Time-to-value in HR depends on *trust*; shipping features on top of F1–F4 would be building on sand. | Strategist's new-feature ideas are Next/Later, not Now. |
| D-003 | **No AI features enter the backlog in this cycle.** | None are evidenced against a real problem; the domain is regulation-heavy. | (a) explore AI assistant now; (b) defer behind problem + compliance gate. | Charter §1 / Strategist guardrail: no AI without a genuine problem and EU AI Act / GDPR Art. 22 safeguards. | Keeps scope honest; revisit in Phase 4. |

---

## 10. Immediate next actions

1. **All specialists:** read your "reads first" set (`00_README.md` table), then execute your T-* tasks above and report back in Charter §6 format.
2. **Product owner:** answer §7 Q1–Q3 (deployment status, login trust model, first-customer intent) — these unblock accurate severities.
3. **Delivery:** produce the first Release Gate table (expected **NO-GO**) and seed the risk/dependency registers.
4. **SPM (me):** on receiving the reports — challenge unevidenced claims, reconcile conflicts, update the Product Health Scorecard + Maturity Assessment, and re-task for Phase 0 execution.

*Standing reminder to the whole team:* engineering changes obey `CLAUDE.md` — the feature-access model, company
scoping, org-change invariants, and the **regression flow-test discipline** are not negotiable, and no change is
"done" until pytest + the regression flow test pass.
