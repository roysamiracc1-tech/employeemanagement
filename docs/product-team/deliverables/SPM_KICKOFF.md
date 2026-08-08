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

> **⚠️ Superseded in part by Decision D-004 (2026-08-09, §9).** The P0 items below keep their *severity* but
> are **re-sequenced to the final stage (S5)**, after all requirements are finalised and implemented. The
> priority column below reads "how bad is it"; the sequencing now lives in
> `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` §E (stages S1–S5). Severity ≠ order.

| Priority | Items | Rationale | Sequencing (D-004) |
|---|---|---|---|
| **P0 (gate-blocking)** | F1/KAN-148 auth · F2/KAN-149 CSRF · F3/KAN-150+173 output-escaping · F4/KAN-151 HTML/upload sanitisation | No product touching employee PII ships without real auth, CSRF, and output-escaping. These block the Production-Ready gate. | **S5 — final phase.** Cross-cutting (~44 endpoints, every DOM builder); doing them before the functional surface is frozen means paying for them twice. Snap back to *now* on triggers T1–T4. |
| **P1 (before production)** | F10/KAN-168 real-DB test tier · F8/KAN-155 atomic writes · F31/KAN-153 required DB config · KAN-166 migration tool · KAN-170 coverage floor | Correctness & confidence: prove the SQL, make composite writes atomic, make the schema/CI trustworthy. | **S2 — now.** These *reduce* the cost of a churning functional backlog; KAN-155 is a hard dependency of EP35-S2 bulk import. |
| **P2 (production readiness)** | F7/KAN-159 connection pool · F16/KAN-160 feature-access cache · F22/KAN-156 N+1s · F24/KAN-158 directory pagination · F20/F21 a11y (KAN-174/175) | Reliability, performance, and accessibility for a real tenant at real size. | Perf items **S2/S3**; a11y retro-fit **S5 pending Q5** (a11y applied as a *design standard* to new screens meanwhile). |
| **P3 (scale / polish)** | F18/KAN-162 object storage · F19/KAN-163 bounded workers · F17/KAN-161 push-not-poll · F26/KAN-172 JS module extraction · EP34 factory/Blueprints | Needed for multi-instance scale and maintainability, not for a first pilot. | Later, except **KAN-178 app factory (S2)** and **KAN-172 shared JS modules (S5, with the escaping work — same code)**. |
| **P4 (strategic / future)** | Integrations (SSO/SCIM, HRIS import, calendar), and any AI/automation — **only** behind the Strategist's problem-first + compliance gate. | Deferred until the foundation is safe and a real problem is evidenced. | **SSO/OIDC is promoted to P0/S5** — it *is* the KAN-148 auth solution. SCIM/HRIS/AI unchanged. |

---

## 5. Phased roadmap (summary)

Aligned to the Delivery role's phase model (`06_*`) and the existing EP28–34 mapping. **No calendar dates** —
targets are stated as exit criteria and dependencies, per the Delivery guardrail. Sequencing, not scheduling.

> **⚠️ Revised by D-004 (2026-08-09).** Phase 0 is **split**: its non-security half runs now, its security half
> becomes the final pre-production phase. The authoritative stage plan is now
> `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` §E (**S1 requirements → S2 enablers → S3 build → S4 freeze →
> S5 security/hardening**). The table below is retained and annotated rather than rewritten, so the original
> reasoning stays auditable.

| Phase | Objective | In scope | Exit criteria | Depends on |
|---|---|---|---|---|
| **Phase 0 — Foundation & Hardening** *(SPLIT by D-004)* | Make the platform reproducible now; safe to expose last. | **Now (S2):** EP31 schema/migrations (F9, KAN-166/167) · EP32 CI + real-DB tier (F10–F12) · EP29 KAN-155 · EP34 KAN-178 · EP28 **KAN-153 only**. **Deferred to S5:** EP28 security (F1–F4) | *Now:* schema rebuildable from repo; real-DB integration tier green in CI; atomic writes in place; **vacation round-trip demonstrable end-to-end**. *S5:* real auth (via SSO), CSRF on all unsafe routes, escaping + upload/HTML sanitisation complete. | §7 Q1 answer **holds** (demo-grade, synthetic data). Triggers T1–T4 void the split. |
| **Phase 1 — MVP / GA-lite (first customer-ready slice)** *(now the main body of work — S1+S3)* | Finalise the requirements, then build the functional product. | Close functional scope (EP35–EP39, EP41 acceptance criteria); build it; harden the two flagship flows for correctness; **WCAG 2.2 AA applied as a design standard on new screens** (retro-fit sweep held to S5, Q5) | Functional scope signed off and **implemented**; pytest + regression flow test green per `CLAUDE.md`; passes **UAT for in-scope personas** (HR admin, manager, employee) **using demo personas** — that is the supported login path until S5; ops runbook + docs exist. | S2 enablers; UAT cohort + environment. |
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

**D-004 does not change this verdict.** Re-sequencing the security work to S5 changes *when* we reach the gate,
not *whether* it blocks. Expect the Production gate to read NO-GO for longer than the original plan implied —
that is the accepted, explicit cost of building the functional product first.

**Conditions to move the Production gate to GO** (unchanged): close KAN-148/149/151 and finish KAN-150→173;
land the real-DB integration tier (KAN-168) so the SQL behind those changes is actually verified; UAT signs off
the two flagship flows for in-scope personas. **Added by D-004:** the S4 feature freeze must be declared before
S5 starts, otherwise the hardening sweep is incomplete by construction.

---

## 9. Decision Log (opened today)

| # | Decision | Context | Options considered | Rationale | Impact |
|---|---|---|---|---|---|
| D-001 | Treat the app as **pre-first-customer / hardening-first** until told otherwise. | No customer, deployment, or timeline is documented (§1, §7). | (a) assume live prod → all F1–F4 live P0; (b) assume demo → F1–F4 gate-blockers; (c) block until answered. | Picking (b) lets the team make progress on the right work now, while §7 Q1–Q3 are chased, without overstating incident severity. Re-evaluated the moment §7 is answered. | Sets P0 framing in §4; roadmap starts at Phase 0. |
| D-002 | ~~**Phase 0 before any new features.**~~ **REVERSED by D-004 (2026-08-09)** for the *security* half only; the reproducibility/testing half stands. | Feature set is already broad (EP1–EP27 ✅); risk is in security/reproducibility, not missing features. | (a) build Phase-1 features now; (b) harden first. | Original rationale: time-to-value in HR depends on *trust*. **What changed:** the trust argument bites at the moment of real exposure, and the app is still demo-grade with synthetic data (D-001) — so the cost of hardening a moving surface twice outweighs the benefit of hardening it early. | Superseded — see D-004. Schema/CI/data-layer enablers remain "before features"; security does not. |
| D-003 | **No AI features enter the backlog in this cycle.** | None are evidenced against a real problem; the domain is regulation-heavy. | (a) explore AI assistant now; (b) defer behind problem + compliance gate. | Charter §1 / Strategist guardrail: no AI without a genuine problem and EU AI Act / GDPR Art. 22 safeguards. | Keeps scope honest; revisit in Phase 4. |
| **D-004** *(2026-08-09)* | **Security & login (EP28 + EP40-S1 SSO) move from FIRST to LAST — executed as a single sweep (S5) after all requirements are finalised and implemented.** **Reverses D-002** ("Phase 0 before any new features"). | Product-owner direction: security and login add complexity while requirements are still moving. Evidence supporting it: KAN-149 spans **~44 state-changing endpoints**, KAN-150/173 spans **every `innerHTML` builder across 7+ templates**, and the remaining functional epics (EP35 import, EP38 lifecycle, EP39 accruals, EP37 gaps) each **add new endpoints and DOM builders to those same surfaces**. Email-only login is a confirmed deliberate demo shortcut (§7 Q2) and the one-click personas are how the team, UAT and stakeholders exercise 4 roles × 2 tenants. | (a) harden first, as originally planned in D-002; (b) harden continuously alongside each feature; (c) **build the functional product, freeze it, then harden once**; (d) refuse to defer. | (a) and (b) pay for the same cross-cutting work twice or more, and re-open escaping regressions on every new screen; (d) is not justified while the app is demo-grade, localhost-only and running **synthetic data** (D-001 still holds). (c) is cheaper and yields a *more complete* sweep, because a frozen surface can actually be swept exhaustively. Deferral is safe **only** while the demo-grade assumption holds — hence the trigger clause. | Phase 0 splits: enablers (EP31/32/29/34 + KAN-153) stay Now; EP28 + EP40-S1 become the final phase S5. **Production gate stays NO-GO and stays blocking** — only its arrival moves. **Triggers T1–T4** (external reachability · real PII · named customer/prospect on real data · any account outside the build team) escalate EP28 back to live P0 immediately. Delivery owns those triggers in the Risk Register (Q6). Opens Q5 (does the a11y retro-fit move with it?). |

---

## 10. Immediate next actions

1. **All specialists:** read your "reads first" set (`00_README.md` table), then execute your T-* tasks above and report back in Charter §6 format. **Re-tasking under D-004 is in `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` §G — that supersedes the ordering here.**
2. **Product owner:** answer §7 Q1 and Q3 (deployment status, first-customer intent) — Q1 now also **validates the D-004 deferral**, since any "yes, it's exposed" answer trips trigger T1. Q2 is closed.
3. **Delivery:** produce the first Release Gate table (expected **NO-GO**) and seed the risk/dependency registers — **including D-004 triggers T1–T4 with a named owner.**
4. **SPM (me):** on receiving the reports — challenge unevidenced claims, reconcile conflicts, update the Product Health Scorecard + Maturity Assessment, and re-task for **S1/S2** execution (not the original Phase 0).

*Standing reminder to the whole team:* engineering changes obey `CLAUDE.md` — the feature-access model, company
scoping, org-change invariants, and the **regression flow-test discipline** are not negotiable, and no change is
"done" until pytest + the regression flow test pass.
