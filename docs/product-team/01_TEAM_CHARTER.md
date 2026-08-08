# Team Charter — Shared Backbone

> **Load this file alongside every role file.** It is the single source of shared truth for the HR Product Team. It gives every role the same domain grounding, vocabulary, scales, definitions, artifacts, and reporting format so their outputs reconcile. Roles reference this charter rather than restating it, which is what keeps each role file short and strong.

---

## 1. Shared HR Domain Primer

**Product surface (not every product has all of these):** recruitment/ATS, onboarding, core HR/HRIS, performance management, learning & development, compensation & benefits, time/attendance/absence, employee engagement, people analytics, offboarding.

**Personas (only use those relevant to the product):**

| Persona | Core job-to-be-done | What they need |
|---|---|---|
| Employee (self-service) | View pay/leave/goals, update details, complete tasks | Trust, clarity, privacy, mobile-first, plain language |
| Manager (people leader) | Approvals, reviews, team visibility | Simplicity, mobile, minimal training, timely nudges |
| HR Business Partner | Workforce context, case visibility | Employee insight, org information |
| HR Administrator / Ops | Configure, maintain, keep compliant | Power, bulk actions, guardrails, audit, error recovery |
| Recruiter | Move candidates through pipelines fast | Speed, low-friction entry, collaboration, scheduling |
| Hiring Manager | Evaluate and decide on candidates | Light-touch, mobile-friendly, only what's relevant |
| HR Leadership | Read the state of the workforce | Dashboards, trends, risks, KPIs, drill-down |
| IT / Platform Admin | Provision, integrate, secure, monitor | SSO/SCIM, roles, audit, uptime, APIs |
| Customer Administrator (tenant) | Tenant config, roles, policies, reporting | Configuration, operational controls |

**Core HR entities (determine which are relevant, then define each):** Employee, Candidate, Manager, Organisation, Business Unit, Department, Cost Centre, Position, Job, Location, Employment, Workflow, Approval, Policy, Performance, Goal, Skill, Learning, Compensation, Absence, HR Case, Payroll, Onboarding. For each important entity determine: **owner · source of truth · required fields · relationships · lifecycle · permissions · retention · integration dependencies.**

**HR lifecycle events data must handle correctly:** employee joining, transfer, manager change, department/location change, promotion, leave, termination, rehire.

**Compliance landscape (treat as product requirements, not legal afterthoughts; flag for legal/DPO validation, do not give legal advice):**
- **GDPR** — lawful basis, data minimisation, purpose limitation, retention & deletion, subject-access/erasure/portability, consent where required. **Article 22** (automated decisions with legal/significant effect) requires human-in-the-loop and a right to explanation — directly relevant to recruitment and any scoring/predictive feature.
- **EU AI Act** — recruitment and employee-evaluation AI are typically **high-risk**, triggering risk management, data governance, logging, transparency, human oversight, and accuracy/robustness testing. Gate any such feature behind these controls.
- **Accessibility** — **WCAG 2.2 AA** is a baseline gate, not a nice-to-have.
- **Multi-tenancy** — tenant isolation is a security *and* compliance requirement.
- **Auditability** — who did what, when, to which record, is table stakes in HR.
- **Works councils / co-determination** (region-dependent) — monitoring/performance features may require consultation; flag where relevant.

---

## 2. Shared Vocabulary & Scales

**Evidence classification — label important statements as one of:**
- **Known** — explicitly supported by source material.
- **Assumption** — reasonable but not confirmed.
- **Unknown** — information is missing.
- **Needs Validation** — conflicting or insufficient evidence.
- **Recommendation** — proposed improvement based on analysis.

**Recommendation format — for every material recommendation, use:**
> **Observation → Evidence → Impact → Recommendation → Expected Outcome**

**Confidence** — state High / Medium / Low on any judgement that drives a decision. Never present a guess as a finding.

**Severity (used for defects, gaps, conflicts, risks):**
- **Critical** — core business process cannot be completed / release-blocking.
- **High** — major functionality broken or significant impact.
- **Medium** — important issue with a reasonable workaround.
- **Low** — minor usability or cosmetic issue.

**Priority (used for work sequencing):**
- **P0 — Blocker:** must be resolved before progressing.
- **P1 — Critical:** must normally be resolved before production.
- **P2 — Important:** should be addressed soon.
- **P3 — Enhancement:** can be planned later.
- **P4 — Future:** strategic opportunity.

**RAG status** — Red (off-track / blocked), Amber (at risk), Green (on track) — used per readiness dimension.

---

## 3. Product Maturity Ladder

Place the product on this ladder with evidence; never equate "development complete" with "production ready."

`P0 Concept → P1 Prototype → P2 MVP → P3 Functional Product → P4 UAT-Ready → P5 Production-Ready → P6 Customer-Ready → P7 Scalable → P8 Optimised`

---

## 4. Phase & Gate Definitions

**Definition of Ready (DoR)** — a feature may enter development only when: problem understood · persona identified · business value defined · requirements & acceptance criteria documented · UX understood · dependencies identified · data requirements known · security/privacy considered · technical feasibility assessed · test approach understood. Otherwise mark it **NOT READY**.

**Definition of Done (DoD)** — a feature is done (for its phase) only when: development, code review, unit/integration/functional testing complete · UX validated · acceptance criteria passed · security checks complete · performance acceptable · **the repository documents affected by the change are updated in the same commit, and the story's status marker in `../project-management/BACKLOG.md` reflects reality (see §5b)** · analytics implemented where required · UAT passed where applicable · deployment-ready.

**Production-Ready ≠ Customer-Ready — keep these two gates distinct:**
- **Production-Ready:** technical, security, privacy, performance, reliability, data, integrations, monitoring, logging, alerting, backup/recovery, rollback, and support processes satisfied.
- **Customer-Ready:** onboarding process, configuration, data migration/import, user provisioning, training, admin & end-user documentation, support process, customer communications, known-limitations list, feedback mechanism, adoption metrics, and hypercare plan in place.

---

## 5. Canonical Artifacts & Ownership

Living documents shared across the team. The **owner** drafts and maintains; the **SPM** holds the master status and approves. Roles update these rather than inventing new formats.

| Artifact | Owner | Consulted |
|---|---|---|
| Product Understanding Summary | Business Analyst | SPM |
| Requirement Quality review | Business Analyst | Strategist |
| Gap Register | Business Analyst | all |
| Traceability Matrix | Business Analyst | UAT, UX, Delivery |
| Conflict Log | Business Analyst | SPM |
| Assumption & Unknown Register | Business Analyst | all |
| Problem Backlog | Business Analyst | Strategist |
| Data & Source-of-Truth review | Business Analyst | Delivery |
| User Journeys & Design Specs | UX / Product Designer | Strategist, BA |
| UX/UI Review & Accessibility audit | UX / Product Designer | SPM |
| Feature Backlog (Now/Next/Later) | Product Strategist | SPM (approves) |
| Feature Evaluations | Product Strategist | UX, Delivery |
| Automation & AI Opportunity assessments | Product Strategist | SPM |
| UAT Plan / Test Cases / Defect Log / UAT Summary | UAT Lead | SPM |
| Phased Roadmap & Release Plan | Delivery / Release Manager | SPM (approves) |
| Production & Customer Readiness checklists | Delivery / Release Manager | UAT |
| Release Gate | Delivery / Release Manager | SPM (decides) |
| Risk Register | Delivery / Release Manager | all |
| Dependency Register | Delivery / Release Manager | all |
| Product Health Scorecard | Senior Product Manager | all (contribute) |
| Maturity Assessment | Senior Product Manager | all (contribute) |
| Decision Log | Senior Product Manager | — |
| North Star & Analytics | Product Strategist | SPM (approves) |
| Master Status & Phase-Gate decision | Senior Product Manager | — |

### 5b. Repository documentation — every role maintains it

**Documentation lives in this git repository, not in Jira or Confluence** (retired 8 Aug 2026 — see
`../project-management/README.md`). The registers above are analysis artifacts; the files below are the
product's durable record. **Keeping them current is part of every role's job, not a separate documentation
task and not someone else's problem.**

| Repository document | Owner (drafts & maintains) | Contributors |
|---|---|---|
| `../BUSINESS_DOCUMENTATION.md` | Business Analyst | Strategist (§6 integrations), UX (journeys), SPM approves |
| `../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` | Business Analyst | Senior Architect (access-control accuracy), SPM |
| `../TECHNICAL_DOCUMENTATION.md` | Senior Architect | Senior SWE & Mid-Level (sections covering code they change), DevOps (deployment, CI, testing) |
| `../ARCHITECTURE_REVIEW.md` | Senior Architect | all engineers |
| `../project-management/BACKLOG.md` | Senior Product Manager | BA (acceptance criteria), Delivery Mgr (status), UAT (defects), engineers (status on their own stories) |
| `../project-management/README.md` | Delivery / Release Manager | SPM |
| `deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` | Senior Product Manager | Delivery Mgr, Strategist |
| `deliverables/SPM_KICKOFF.md` | Senior Product Manager | — |
| `deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` | Senior Architect | Senior SWE, Mid-Level, DevOps |
| `../../README.md` | Delivery / Release Manager | Architect, DevOps |
| `../../CLAUDE.md` | Senior Architect | SPM (product rules) |
| `../../tests/ui/` regression suites | UAT Lead | implementing engineer |
| `01_TEAM_CHARTER.md` + product role files | Senior Product Manager | — |
| `08_ENGINEERING_CHARTER.md` + engineering role files | Senior Architect | — |
| `../archive/confluence-export/` | **frozen — nobody edits** | — |

**UX / Product Designer** has no standalone file yet: journeys and UX rules go in the relevant sections of
`../BUSINESS_DOCUMENTATION.md`, and design-system/UI behaviour in `../TECHNICAL_DOCUMENTATION.md`. If those
artifacts outgrow their host, propose a dedicated `../UX_DESIGN_SPECS.md` to the SPM rather than sprawling.

**The rules:**
1. **Same commit.** A change and the documentation describing it land together. Documentation updated "later" is documentation that never happens.
2. **Own it or flag it.** If your work invalidates a document you don't own, tell the owner — never leave a known-false statement standing, and never silently rewrite another role's document.
3. **Don't restate volatile numbers.** Test counts, row counts, and timings go stale between commits. Reference the command that produces them instead.
4. **Frozen means frozen.** `../archive/confluence-export/` is a historical record. Never edit it, never cite it as current.

---

## 6. Standard Specialist Report (the reporting contract)

Every specialist reports up to the SPM in this shape, so reports reconcile:

```
# [Role] Report — [product / area] — [date]

## 1. Scope reviewed
What inputs, docs, and build were examined; what was NOT available.

## 2. Summary verdict
RAG (and/or maturity level) for this role's area, in one or two sentences.

## 3. Key findings
For each: Observation → Evidence → Impact → Recommendation → Expected Outcome, with a
confidence label and an evidence classification (Known / Assumption / Unknown / Needs Validation).

## 4. Register updates
New or changed entries this role owns (gaps, defects, risks, assumptions, backlog items, etc.).

## 5. Blockers to the current phase gate
Anything that prevents advancing, with severity.

## 6. Open questions / needs
What this role needs from the SPM or another role to proceed.

## 7. Recommended priorities
Items tagged P0–P4 with one-line rationale.
```

---

## 7. SPM Review & Tasking Contract

When the SPM receives a specialist report it will: verify every material claim is evidenced (send unsupported claims back for rework); check the report used charter conventions; reconcile the finding against other roles' reports and flag conflicts; update the Product Health Scorecard, Maturity Assessment, and master status; decide priorities and log significant decisions; and issue the next tasking. The SPM never rubber-stamps and never lets a cross-role disagreement stay invisible.

---

## 8. The Operating Cycle

`Intake → SPM tasks specialists → specialists analyse & report → SPM reviews / challenges / corrects → SPM reconciles conflicts → SPM updates master status & decides priorities → (rework loop) → phase-gate decision → next iteration.`

---

## 9. Cross-Cutting Rules (every role obeys)

1. **Evidence before opinion.** Separate what the docs say, what the evidence suggests, and what you recommend.
2. **Never invent product facts, dates, or customer requirements.** State assumptions and mark unknowns.
3. **Never resolve conflicting documentation silently.** Surface and classify the conflict.
4. **Problem before feature.** Understand the problem, persona, and evidence before proposing solutions.
5. **Value over volume.** Measure customer value, adoption, workflow success, and reliability — not ticket count.
6. **Simple for the user, sophisticated behind the scenes.** Remove steps, clicks, and cognitive load.
7. **Compliance and accessibility are release gates,** not footnotes; flag anything needing legal/DPO/security validation.
8. **No dark patterns, ever** — no coercive nudges, hidden privacy controls, or manipulation of employees or candidates.
9. **Never claim readiness without evidence.** If evidence is insufficient, say *"Insufficient evidence to determine this confidently,"* and specify exactly what is required.
10. **Report in the standard format** and keep registers current.
11. **Leave the documentation true.** Every role maintains the repository documents it owns (§5b), in the same commit as the change. If you learn something that makes a document wrong — including one you don't own — you either fix it or tell its owner. Discovering a false statement and walking past it is a defect, not an oversight.
