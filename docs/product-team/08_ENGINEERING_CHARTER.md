# Engineering Charter — Shared Backbone (Engineering Team)

> **Load this file, plus the product `01_TEAM_CHARTER.md`, alongside every engineering role file.** The engineering team **inherits** the product Team Charter and **adds** engineering-specific standards and the cross-team interface. This is what connects the two orgs: one shared language, two specialisms.

---

## 1. Inheritance — what you take from the product Team Charter

You inherit and obey, unchanged: the **evidence classification** (Known / Assumption / Unknown / Needs Validation / Recommendation), the **recommendation format** (Observation → Evidence → Impact → Recommendation → Expected Outcome), the **severity** and **priority (P0–P4)** scales, **RAG** status, **confidence** labels, the **maturity ladder**, **Definition of Ready / Definition of Done**, the **Production-Ready vs Customer-Ready** distinction, the **standard report format** (Charter §6), the **operating cycle**, and the **cross-cutting rules** (evidence before opinion; never invent facts/dates; never resolve conflicts silently; no dark patterns; compliance & accessibility are gates; never claim readiness without evidence).

This Engineering Charter adds only what's engineering-specific below.

---

## 2. Technology Stack & Conventions

**Confirm the actual stack from the repository and technical docs before assuming — the following are defaults to adapt, not impose:**
- **Backend:** Python (FastAPI / Flask) and/or Java (Spring). REST APIs, versioned, contract-first where practical.
- **Frontend:** React + TypeScript.
- **Data:** PostgreSQL as the system of record; migrations are versioned and reversible.
- **General:** 12-factor app principles; config via environment, secrets never in code; stateless services; idempotent operations; structured logging; API backward compatibility within a major version.

Match the product's real stack (from Samir's context this is commonly Python/Flask, Node/TypeScript, .NET, React/Next.js, PostgreSQL) — verify per project.

---

## 3. Architecture Principles

1. **Simplest thing that works.** Avoid premature complexity and speculative generality; add abstraction when a second real case demands it.
2. **Separation of concerns / bounded contexts.** Clear module and service boundaries aligned to the HR domain (recruitment, core HR, performance, etc.).
3. **Multi-tenant isolation by design.** Tenant boundaries enforced at data and access layers — a security *and* compliance requirement (connects to the HR product's tenancy needs).
4. **Security and privacy by design.** AuthN/AuthZ, least privilege, input validation, output encoding, encryption in transit and at rest, audit logging — designed in, not bolted on.
5. **Observability by design.** Every service emits structured logs, metrics, and traces; failures are diagnosable.
6. **Data integrity & source of truth.** One owner per data element; referential integrity; correct behaviour across HR lifecycle events (join, transfer, promotion, leave, termination, rehire — see product Charter §1).
7. **Backward compatibility & safe change.** Contracts evolve without breaking consumers; migrations are reversible; changes are feature-flagged where risk warrants.
8. **Design for failure.** Timeouts, retries with backoff, idempotency, graceful degradation, and recovery for every integration.
9. **Compliance controls are implemented here.** Human-in-the-loop, explainability hooks, audit trails, consent/retention/erasure mechanisms for GDPR Art. 22 and EU AI Act high-risk features are engineering deliverables, not just policy (see product Charter §1).
10. **Record significant decisions.** Use Architecture Decision Records (ADRs).

---

## 4. Engineering Definition of Done (code-level — extends the product DoD)

A change is done only when: it meets the acceptance criteria; code is **peer-reviewed and approved**; **unit and integration tests** are added and passing; linting and **security/dependency scans** show no critical findings; **API specs and the affected sections of `../TECHNICAL_DOCUMENTATION.md` are updated in the same commit, and the story's status marker in `../project-management/BACKLOG.md` is corrected** (§9, product Charter §5b); **migrations reversible**; **observability** (logs/metrics/traces) added for new paths; performance within the agreed budget; **frontend meets WCAG 2.2 AA** for changed UI; secrets handled correctly; change is **backward compatible** (or a migration/deprecation path is documented); and it is **feature-flagged** where rollout risk warrants.

---

## 5. Code Review Protocol

- **Every change goes through a pull request**; no direct merges to the main branch.
- **Who reviews:** Senior Software Engineers review Mid-level PRs; the Senior Architect reviews architecture-impacting or cross-cutting changes (schema, public API, security boundaries, tenancy).
- **Reviewers check:** correctness vs acceptance criteria, tests present and meaningful, security/tenant-isolation, error/edge/state handling, performance, readability/maintainability, adherence to ADRs and standards, no untracked tech debt.
- **Keep PRs small** and single-purpose. "Approved" means all of the above are satisfied — not just "looks fine."

---

## 6. Testing Strategy

Follow the testing pyramid: **many unit tests, fewer integration tests, few end-to-end tests.** Coverage should be meaningful, not vanity. **Contract tests** for integrations; **security tests** for auth and tenancy. Test data is **synthetic or anonymised — never real employee PII** (connects to the product Charter and the UAT Lead). Engineering fills the **Test Case** link in the BA's traceability matrix.

---

## 7. Security & Privacy Baseline

AuthN/AuthZ with RBAC · enforced tenant isolation · input validation and output encoding · OWASP-aware coding · secrets in a manager (never in code or logs) · dependency and container scanning · encryption at rest and in transit · comprehensive audit logging · GDPR data handling implemented in code (minimisation, retention, erasure hooks, DSAR support). Flag anything needing security/DPO validation; engineering implements controls, product/legal owns the policy.

---

## 8. Branching & Environments

Default to a simple, CI-gated flow (trunk-based or short-lived feature branches; adapt per project). Environments: **dev → UAT → staging → production**, kept as close to parity as practical. CI must pass (build, tests, lint, security scan) before merge; deployment is automated and reversible.

---

## 9. Engineering Artifacts & Ownership

| Artifact | Owner | Consulted |
|---|---|---|
| Architecture Decision Records (ADRs) | Senior Architect | all engineers |
| Technical Design Docs | Senior Architect / Senior SWE | product BA, UX |
| API Specifications | Senior SWE (impl) / Architect (standards) | BA, front-end |
| Data Model & Migrations | Senior SWE | Architect, BA |
| Test Suites | implementing engineer | Architect |
| Technical Debt Register | Senior Architect | all engineers |
| Technical Risk Register | Senior Architect | product Delivery Mgr |
| CI/CD Pipelines | Senior DevOps | Architect |
| Infrastructure-as-Code | Senior DevOps | Architect |
| Observability dashboards & alerts | Senior DevOps | all |
| Runbooks & DR plan | Senior DevOps | Delivery Mgr |
| Deployment & rollback procedures | Senior DevOps | Delivery Mgr |

**Repository documentation is an engineering artifact too.** You inherit product Charter **§5b** in full —
documentation lives in git, and maintaining it is part of building, not a follow-up chore. Engineering's
share of that map:

| Repository document | Owner | Contributors |
|---|---|---|
| `../TECHNICAL_DOCUMENTATION.md` | Senior Architect | **Senior SWE / Mid-Level: the sections covering code you change** — schema, API reference, helpers, feature sections |
| `../ARCHITECTURE_REVIEW.md` (findings `F1`–`F31`) | Senior Architect | all engineers — close a finding by updating it, don't just fix the code |
| `../../CLAUDE.md` (engineering invariants) | Senior Architect | anyone who changes an invariant it documents |
| `deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` | Senior Architect | Senior SWE, Mid-Level, DevOps (task status) |
| `../TECHNICAL_DOCUMENTATION.md` deployment / CI / testing sections | Senior DevOps | Architect |
| `../project-management/BACKLOG.md` — status markers on your own stories | (see product Charter §5b) | implementing engineer |

**Never** call the Atlassian/Jira/Confluence tooling for project documentation, and never link to
`*.atlassian.net` — retired 8 Aug 2026, all such URLs are dead. `../archive/confluence-export/` is frozen.

---

## 10. Cross-Team Interface — how Product ↔ Engineering connect

**SPM and Senior Architect are peer leads.** Product owns *what* and *why* and priority; engineering owns *how* and feasibility. Scope-versus-feasibility trade-offs are negotiated between them and recorded in the SPM's **Decision Log**. A release is gated jointly: the SPM's phase gate and the Delivery Manager's release gate both **consume the Architect's technical-readiness verdict and DevOps's production-readiness evidence.**

**Inbound to engineering:**
- From **Business Analyst:** requirements, acceptance criteria, data model, and the traceability matrix. Engineering checks these against the **Definition of Ready** and flags gaps/ambiguities/conflicts **back to the BA** rather than guessing.
- From **UX / Product Designer:** design specs, interaction behaviour, and required states. Front-end implements them and flags any infeasibility back to UX.
- From **SPM / Delivery Manager:** the prioritised, ready backlog, the current phase, and the non-functional requirements.

**Outbound from engineering:**
- To **SPM:** feasibility assessments, technical designs, estimates, and a **technical-readiness report** that feeds the phase gate.
- To **Business Analyst:** the filled **Technical Implementation** and **Test Case** links in the traceability matrix.
- To **UAT Lead:** deployed builds to the UAT environment, with release notes and known limitations; and fixes for UAT defects.
- To **Delivery Manager / DevOps coordination:** production-readiness evidence, deployment strategy, and rollback.

**Reporting.** Engineering reports up to the Senior Architect using the **standard report format** (product Charter §6); the Architect integrates these and reports technical readiness across to the SPM. Same format, so everything reconciles.

---

## 11. The Engineering Cycle (mirrors the product cycle)

`Ready backlog in → Architect designs / reviews design → Architect tasks SWEs (Senior for hard/cross-cutting, Mid for well-scoped) and DevOps → engineers build & test & open PRs → review (Senior reviews Mid; Architect reviews architecture-impacting) → Architect integrates & reports technical readiness → (rework loop) → hand off to UAT / release.`
