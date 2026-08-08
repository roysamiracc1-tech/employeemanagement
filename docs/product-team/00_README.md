# HR Product Team — AI Persona System (README)

A modular set of AI role instructions that together act as a product organisation for taking an HR product from its current state to a **production-ready, customer-ready release, in phases**. Instead of one giant prompt, work is split across focused specialist roles that report to a **Senior Product Manager (SPM)**, who reviews their output, corrects it, reconciles conflicts, decides, and runs the cycle again.

## Why it's built this way
- **Focused instructions stay strong.** Loading one role file means the model sees only that role's instructions at full weight — nothing important is buried under unrelated checklists.
- **Modular & maintainable.** Update the UX role without touching UAT.
- **Composable.** Run one specialist in isolation, or run the whole cycle.
- **Consistent.** A shared **Team Charter** gives every role the same vocabulary, scales, definitions, and report format, so their outputs reconcile.

## The team (org chart)
```
                        Senior Product Manager (SPM)
                        orchestrate · review · correct · decide · gate
        ┌───────────────┬───────────────┬───────────────┬───────────────┐
   Business         UX / Product        UAT Lead        Delivery /      Product
   Analyst          Designer                            Release Mgr     Strategist
   gaps · reqs      experience ·        validation ·    roadmap ·       ideas ·
   traceability     journeys · a11y     test · sign-off phases · gates  prioritise
```

## Files
| File | Role | Owns |
|---|---|---|
| `01_TEAM_CHARTER.md` | **Shared backbone (load with every role)** | Domain primer, vocabulary, scales, definitions, artifact ownership, report contract, the cycle |
| `02_SENIOR_PRODUCT_MANAGER.md` | **Senior Product Manager** | Orchestration, review, conflict resolution, prioritisation & roadmap decisions, phase gates, decision log |
| `03_BUSINESS_ANALYST.md` | Business Analyst | Product understanding, requirement quality, gap register, traceability, conflicts, assumptions, problem backlog, data/source-of-truth |
| `04_UX_PRODUCT_DESIGNER.md` | UX / Product Designer | Journeys, design specs, UX/UI review, accessibility, states, microcopy |
| `05_UAT_LEAD.md` | UAT Lead / Tester | UAT plan, test cases, defect log, exit criteria, sign-off |
| `06_DELIVERY_RELEASE_MANAGER.md` | Delivery / Release Manager (Project Manager) | Phased roadmap, production & customer readiness, release gate, risk & dependency registers |
| `07_PRODUCT_STRATEGIST.md` | Product Strategist | Feature ideation & evaluation, prioritisation, automation & AI opportunities, North Star |
| `08_SPM_KICKOFF.md` | **SPM onboarding & first tasking (this project)** | The SPM's intake against the existing docs, maturity read, phased roadmap, and task assignments to each specialist |

## How this maps to THIS project (chain of responsibility)
The team does not start from a blank page. This repository already contains the source material each role must read before acting. The SPM's first act (see `08_SPM_KICKOFF.md`) is to route the team to it:

| Role | Reads first (in this repo) | Produces / maintains |
|---|---|---|
| **All** | `../BUSINESS_DOCUMENTATION.md`, `../TECHNICAL_DOCUMENTATION.md`, `../../CLAUDE.md`, `../../README.md` | — |
| Business Analyst | `../BUSINESS_DOCUMENTATION.md`, `../JIRA_EPICS_AND_STORIES.md` | Gap Register, Traceability, Conflict Log, Problem Backlog |
| UX / Product Designer | `../TECHNICAL_DOCUMENTATION.md` (§7 org tree, §20–22 flows), `../ARCHITECTURE_REVIEW.md` (a11y findings F20/F21) | Journeys, design specs, accessibility audit |
| UAT Lead | `../JIRA_EPICS_AND_STORIES.md`, the two regression suites in `../../tests/ui/` | UAT plan, test cases, defect log, sign-off |
| Delivery / Release Mgr | `../ARCHITECTURE_REVIEW.md`, `../JIRA_EPICS_AND_STORIES.md` (EP28–34) | Phased roadmap, readiness checklists, release gate, risk/dependency registers |
| Product Strategist | `../BUSINESS_DOCUMENTATION.md` (§6 integrations), `../JIRA_EPICS_AND_STORIES.md` | Feature backlog (Now/Next/Later), AI/automation assessments, North Star |
| Senior Product Manager | **everything above** | Health scorecard, maturity assessment, decision log, phase-gate decision |

## How to run it — two modes

**Manual (one chat/tool at a time):**
1. Load `01_TEAM_CHARTER.md` + one specialist role file (e.g. Business Analyst). Give it the product inputs.
2. It returns a **Specialist Report** in the charter's standard format.
3. Load `01_TEAM_CHARTER.md` + `02_SENIOR_PRODUCT_MANAGER.md`, paste the report(s). The SPM reviews, challenges weak evidence, reconciles across reports, decides priorities, and issues the next tasking.
4. Feed that tasking back to the relevant specialist(s). Repeat.

**Agentic (orchestrated, e.g. subagents / an MCP setup):**
- The orchestrator loads Charter + SPM. The SPM dispatches tasks to specialist subagents (each loaded with Charter + its role file), collects their reports, reviews and reconciles, updates the master status, and loops until the phase gate passes.

## The operating cycle
```
Intake → SPM tasks specialists → Specialists analyse & report
   → SPM reviews / challenges / corrects → SPM reconciles conflicts
   → SPM updates master status & decides priorities
   → (rework loop if evidence is weak or gaps remain)
   → Phase-gate decision (GO / CONDITIONAL / NO-GO) → next iteration
```

## Inputs to provide at intake
Business docs (vision, BRD/PRD, personas, requirements, success metrics), the backlog (epics/stories with acceptance criteria), technical docs (architecture, data model, API/integration specs, security & tenancy model, test coverage), access to or a demo of the current build, and constraints (target customers, timeline, capacity, regulatory scope, stack). Missing inputs are not a blocker — every role labels what's Known vs Assumption vs Unknown and states what it needs (see Charter).
