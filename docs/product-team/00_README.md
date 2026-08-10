# HR Product & Engineering — AI Persona System (README)

A modular set of AI role instructions that together act as **two connected organisations** — a **Product org**
and an **Engineering org** — for taking an HR product from its current state to a **production-ready,
customer-ready release, in phases**. Instead of one giant prompt, work is split across focused roles. Each org
has a lead who reviews their team's output, corrects it, reconciles conflicts, decides, and loops. The two orgs
share one language and hand off through a defined interface.

## Why it's built this way
- **Focused instructions stay strong.** Loading one role file means the model sees only that role's instructions at full weight — nothing important is buried under unrelated checklists. Total lines across the system are large, but no single file you load is heavy.
- **Modular & maintainable.** Update the UX role without touching UAT; update DevOps without touching the Architect.
- **Composable.** Run one role in isolation, one org, or the whole system.
- **Consistent.** A shared **Team Charter** gives *every* role — product and engineering — the same vocabulary, scales, definitions, and report format, so their outputs reconcile. The **Engineering Charter** inherits it and adds technical standards.

## The two orgs (org chart)
```
        Senior Product Manager (SPM)  ◄──── peer leads, joint release gate ────►  Senior Architect
        orchestrate · review · gate                                              architecture · standards · review · tech readiness
   ┌──────────┬───────────┬──────────┬──────────┐                    ┌──────────────┬──────────────┬──────────────┐
 Business   UX/Product   UAT Lead   Delivery/   Product        Senior SW       Mid-Level        Senior
 Analyst    Designer                Release Mgr Strategist     Engineers        Engineers        DevOps
 gaps·reqs  UX·a11y      validation roadmap·    ideas·         hard problems·   scoped work·     CI/CD·infra·
 traceab.   ·journeys    ·sign-off  gates       prioritise     review·mentor    escalate early   observ.·release
```

## Files
**Shared + Product org**
| File | Role | Owns |
|---|---|---|
| `01_TEAM_CHARTER.md` | **Shared backbone (load with every role, both orgs)** | Domain primer, vocabulary, scales, definitions, artifact ownership, report contract, the cycle |
| `02_SENIOR_PRODUCT_MANAGER.md` | **Senior Product Manager** | Orchestration, review, conflict resolution, prioritisation & roadmap decisions, phase gates, decision log |
| `03_BUSINESS_ANALYST.md` | Business Analyst | Product understanding, requirement quality, gap register, traceability, conflicts, assumptions, problem backlog, data/source-of-truth |
| `04_UX_PRODUCT_DESIGNER.md` | UX / Product Designer | Journeys, design specs, UX/UI review, accessibility, states, microcopy |
| `05_UAT_LEAD.md` | UAT Lead / Tester | UAT plan, test cases, defect log, exit criteria, sign-off |
| `06_DELIVERY_RELEASE_MANAGER.md` | Delivery / Release Manager (Project Manager) | Phased roadmap, production & customer readiness, release gate, risk & dependency registers |
| `07_PRODUCT_STRATEGIST.md` | Product Strategist | Feature ideation & evaluation, prioritisation, automation & AI opportunities, North Star |

**Engineering org**
| File | Role | Owns |
|---|---|---|
| `08_ENGINEERING_CHARTER.md` | **Engineering backbone (load with every engineering role)** | Inherits the Team Charter; adds stack, architecture principles, code-level DoD, review protocol, testing, security baseline, engineering artifacts, **the product–engineering interface** |
| `09_SENIOR_ARCHITECT.md` | **Senior Architect** (peer to SPM) | Architecture decisions (ADRs), technical standards, review, tech debt & risk registers, technical-readiness verdict |
| `10_SENIOR_SOFTWARE_ENGINEER.md` | Senior Software Engineer (full-stack) | Complex/cross-cutting features, tests, code review, mentoring |
| `11_MIDLEVEL_ENGINEER.md` | Mid-Level Engineer (full-stack) | Well-scoped features, tests, early escalation of ambiguity |
| `12_SENIOR_DEVOPS_ENGINEER.md` | Senior DevOps Engineer | CI/CD, IaC, observability, deployment & rollback, security posture, production-readiness evidence |

**Produced for THIS project** (`deliverables/`)
| File | Produced by | Contents |
|---|---|---|
| `deliverables/SPM_KICKOFF.md` | Senior Product Manager | Intake against the existing docs, maturity read, phased roadmap, task assignments to each product specialist |
| `deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` | Senior Product Manager | Written after driving the running app; Business Goals → Epics → User Stories, ready to fold into `../project-management/BACKLOG.md` |
| `deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` | Senior Architect | Knowledge transfer to the engineering team + user stories subdivided into technical tasks assigned to Senior SWE / Mid-level / DevOps |

## How this maps to THIS project (reads-first / chain of responsibility)
Neither org starts from a blank page — this repo already contains the source material. Read your set before acting:

| Role | Reads first (in this repo) | Produces / maintains | **Repo documents it keeps current** (Charter §5b) |
|---|---|---|---|
| **All** | `../BUSINESS_DOCUMENTATION.md`, `../TECHNICAL_DOCUMENTATION.md`, `../../CLAUDE.md`, `../../README.md` | — | Status markers on stories it touches; flag any document its work makes false |
| Business Analyst | `../BUSINESS_DOCUMENTATION.md`, `../project-management/BACKLOG.md` | Gap Register, Traceability, Conflict Log, Problem Backlog | `../BUSINESS_DOCUMENTATION.md`, `../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`, acceptance criteria in `../project-management/BACKLOG.md` |
| UX / Product Designer | `../TECHNICAL_DOCUMENTATION.md` (§7, §20–22), `../ARCHITECTURE_REVIEW.md` (F20/F21) | Journeys, design specs, accessibility audit | Journey/UX sections of `../BUSINESS_DOCUMENTATION.md`; design-system & UI behaviour in `../TECHNICAL_DOCUMENTATION.md` |
| UAT Lead | `../project-management/BACKLOG.md`, `../../tests/ui/` | UAT plan, test cases, defect log, sign-off | `../../tests/ui/` regression suites; defect & story status in `../project-management/BACKLOG.md` |
| Delivery / Release Mgr | `../ARCHITECTURE_REVIEW.md`, `../project-management/BACKLOG.md` (EP28–34) | Phased roadmap, readiness checklists, release gate, registers | `../project-management/README.md`, `../../README.md`, status markers across `../project-management/BACKLOG.md` |
| Product Strategist | `../BUSINESS_DOCUMENTATION.md` (§6), `../project-management/BACKLOG.md` | Feature backlog, AI/automation assessments, North Star | `../BUSINESS_DOCUMENTATION.md` §6 Integration Points; Now/Next/Later in the roadmap |
| **Senior Product Manager** | all of the above + specialist reports | Scorecard, Maturity, Decision Log, phase gate | `../project-management/BACKLOG.md`, `deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`, `deliverables/SPM_KICKOFF.md`, product role files |
| **Senior Architect** | `../ARCHITECTURE_REVIEW.md` (F1–F31), `../TECHNICAL_DOCUMENTATION.md`, `../../CLAUDE.md`, `../../app/`, `../../database/` | ADRs, tech-debt & risk registers, technical-readiness verdict, task breakdown | `../TECHNICAL_DOCUMENTATION.md`, `../ARCHITECTURE_REVIEW.md`, `../../CLAUDE.md`, `deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md`, engineering role files |
| Senior / Mid Engineer | `../TECHNICAL_DOCUMENTATION.md`, the relevant `app/` module, `../../tests/` | Reviewed, tested code (PRs); traceability Test/Impl links | The sections of `../TECHNICAL_DOCUMENTATION.md` covering code they changed; own story status |
| Senior DevOps | `../../.github/workflows/`, `../TECHNICAL_DOCUMENTATION.md` §10–§11, `../../database/schema.sql` | CI/CD, IaC, observability, release/rollback, prod-readiness evidence | Deployment / env-var / CI / testing sections of `../TECHNICAL_DOCUMENTATION.md`; runbooks & DR plan |

> **Documentation is not a separate workstream.** It lives in git (Jira and Confluence were retired
> 8 Aug 2026 — see `../project-management/README.md`), every role maintains its own share of it, and the
> update lands **in the same commit** as the change it describes. The authoritative map is
> **Team Charter §5b**; Engineering Charter §9 adds engineering's share. `../archive/confluence-export/`
> is frozen — never edited, never cited as current.

## How the two orgs connect
- **SPM and Senior Architect are peer leads.** Product owns *what / why / priority*; engineering owns *how / feasibility*. Scope-vs-feasibility trade-offs are negotiated between them and recorded in the SPM's Decision Log.
- **A release is gated jointly:** the SPM's phase gate and the Delivery Manager's release gate both consume the **Architect's technical-readiness verdict** and **DevOps's production-readiness evidence**.
- **Handoffs (see `08_ENGINEERING_CHARTER.md` §10):** BA → engineering (requirements, acceptance criteria, data model, traceability); UX → front-end (design specs, states); SPM/Delivery → engineering (ready backlog, phase, NFRs). Engineering → BA (implementation + test links in the traceability matrix); engineering → UAT (deployed builds + release notes + defect fixes); DevOps → Delivery Manager (release plan, rollback, monitoring, release gate).
- **One report format.** Everyone reports in the Team Charter §6 standard format, so product and engineering outputs reconcile.

## How to run it — two modes

**Manual (one chat/tool at a time):**
1. Load the relevant charter(s) + one role file, and give it the inputs.
   - Product role → `01_TEAM_CHARTER.md` + the role file.
   - Engineering role → `01_TEAM_CHARTER.md` + `08_ENGINEERING_CHARTER.md` + the role file.
2. It returns a report in the standard format.
3. Load the charter(s) + the lead (SPM for product, Architect for engineering), paste the report(s). The lead reviews, challenges weak evidence, reconciles, decides, and issues the next tasking.
4. Feed that tasking back to the relevant role(s). Repeat. Across orgs, the SPM and Architect exchange their integrated reports at the interface points above.

**Agentic (orchestrated, e.g. subagents / an MCP setup):**
- Two orchestrators (SPM, Architect) each dispatch to their specialist subagents, collect and reconcile reports, and exchange readiness at the interface. Loop until the joint gate passes.

## The operating cycle (both orgs mirror it)
```
Intake → lead tasks the team → members analyse / build & report
   → lead reviews / challenges / corrects → lead reconciles conflicts
   → lead updates master status & decides priorities
   → (rework loop if evidence is weak or gaps remain)
   → interface exchange (product ↔ engineering readiness)
   → joint gate decision (GO / CONDITIONAL / NO-GO) → next iteration
```

## Inputs to provide at intake
Business docs (vision, BRD/PRD, personas, requirements, success metrics), the backlog (epics/stories with acceptance criteria), technical docs (architecture, data model, API/integration specs, security & tenancy model, test coverage), access to or a demo of the current build, and constraints (target customers, timeline, capacity, regulatory scope, and the real tech stack). Missing inputs are not a blocker — every role labels what's Known vs Assumption vs Unknown and states what it needs (see Charter).
