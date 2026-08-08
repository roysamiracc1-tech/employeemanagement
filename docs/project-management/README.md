# Project Management & Documentation — How This Works

**Single source of truth: this git repository.** Business documentation, technical documentation,
the product roadmap, and the backlog all live here as markdown, are edited here, and are versioned
by git history.

**Atlassian was retired on 8 August 2026.** Jira and Confluence are no longer used for this project.
Do not create issues or wiki pages there, and do not link to `roysamiracc1-1777144763345.atlassian.net`
— those URLs are dead.

---

## Where everything lives

| I want to change… | Edit this |
| --- | --- |
| Business processes, rules, roles, retention | [`../BUSINESS_DOCUMENTATION.md`](../BUSINESS_DOCUMENTATION.md) |
| Feature catalogue, access-rights matrices, nav-by-role | [`../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`](../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md) |
| Schema, APIs, architecture, deployment, testing | [`../TECHNICAL_DOCUMENTATION.md`](../TECHNICAL_DOCUMENTATION.md) |
| Epics, user stories, acceptance criteria, delivery status | [`BACKLOG.md`](BACKLOG.md) |
| Business goals → epics → stories, sequencing | [`../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md) |
| Technical task breakdown for the roadmap | [`../product-team/deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md`](../product-team/deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md) |
| Technical debt findings (`F1`–`F31`) | [`../ARCHITECTURE_REVIEW.md`](../ARCHITECTURE_REVIEW.md) |
| Persona/org definitions driving the above | [`../product-team/`](../product-team/) |

Historical Confluence snapshots are frozen in [`../archive/confluence-export/`](../archive/confluence-export/).
They are records, not documentation — never edit them and never cite them as current.

---

## Who maintains what

Every persona in [`../product-team/`](../product-team/) is responsible for keeping its own documents
current — documentation is part of each role's job, not a separate workstream handed to someone else.
The authoritative map is **Team Charter §5b**
([`../product-team/01_TEAM_CHARTER.md`](../product-team/01_TEAM_CHARTER.md)); Engineering Charter §9
([`../product-team/08_ENGINEERING_CHARTER.md`](../product-team/08_ENGINEERING_CHARTER.md)) adds
engineering's share. Summary:

| Document | Owner | Contributors |
|---|---|---|
| [`../BUSINESS_DOCUMENTATION.md`](../BUSINESS_DOCUMENTATION.md) | Business Analyst | Strategist (§6), UX (journeys), SPM approves |
| [`../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`](../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md) | Business Analyst | Senior Architect, SPM |
| [`../TECHNICAL_DOCUMENTATION.md`](../TECHNICAL_DOCUMENTATION.md) | Senior Architect | Senior SWE & Mid-Level (code they change), DevOps (deploy/CI/testing) |
| [`../ARCHITECTURE_REVIEW.md`](../ARCHITECTURE_REVIEW.md) | Senior Architect | all engineers |
| [`BACKLOG.md`](BACKLOG.md) | Senior Product Manager | BA (acceptance criteria), Delivery Mgr (status), UAT (defects), engineers (own stories) |
| `README.md` (this file) | Delivery / Release Manager | SPM |
| [`../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`](../product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md) | Senior Product Manager | Delivery Mgr, Strategist |
| [`../product-team/deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md`](../product-team/deliverables/ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md) | Senior Architect | Senior SWE, Mid-Level, DevOps |
| [`../../README.md`](../../README.md) | Delivery / Release Manager | Architect, DevOps |
| [`../../CLAUDE.md`](../../CLAUDE.md) | Senior Architect | SPM (product rules) |
| `../../tests/ui/` regression suites | UAT Lead | implementing engineer |
| [`../archive/confluence-export/`](../archive/confluence-export/) | **frozen — nobody** | — |

**The rules that make this work:**

1. **Same commit.** The change and the documentation describing it land together.
2. **Own it or flag it.** If your work makes a document you don't own false, tell the owner. Never
   silently rewrite another role's document; never walk past a known-false statement.
3. **Don't restate volatile numbers.** Test counts, row counts, and timings go stale between commits —
   reference the command that produces them instead.
4. **It's a gate, not a chore.** "Documentation updated" is in the Definition of Done, in the
   Production and Customer Readiness checklists, and in the Release Gate table. Stale documentation is
   a gate finding with a severity.

---

## Identifiers

* **Epics** are `EP1` … `EP34`.
* **Stories** are `KAN-###`. The prefix is a historical artefact of the retired Jira project.
  These are now plain local IDs — they are **not** links and there is nothing to click through to.
  They are kept because `../ARCHITECTURE_REVIEW.md` and the product-team deliverables reference them.
* **Architecture findings** are `F1` … `F31`, defined in `../ARCHITECTURE_REVIEW.md`.

New stories continue the `KAN-###` sequence. Take the next free number from the bottom of
[`BACKLOG.md`](BACKLOG.md) — there is no server assigning them, so check before reusing one.

---

## Status tracking

Status lives in the backlog as a column plus a per-story marker:

| Marker | Meaning |
| --- | --- |
| ✅ | Done — delivered and on `main` |
| 🟡 | In progress — partially delivered |
| ⬜ | Planned — not started |

Because nothing enforces these markers, they drift. When you touch a story, update its marker in the
same commit as the code. Git history is the audit trail: `git log --follow docs/project-management/BACKLOG.md`
shows who changed what status and when, which is the one thing the old Jira board did that markdown
does not do automatically.

---

## Workflow for a documentation or roadmap update

1. Edit the relevant markdown file(s) above.
2. Keep the change and any related code change in the **same commit** so docs never drift from code.
3. Commit on a branch, then push. Documentation-only changes do not need the regression flow test;
   changes that touch code do — see `CLAUDE.md`.

```bash
git add docs/
git commit -m "Docs: <what changed and why>"
git push
```

---

## Known trade-offs of running this in git

Recorded honestly so nobody is surprised later:

* **No board, no queries.** There is no sprint view, burndown, or JQL. Use `grep`, and the status
  markers above.
* **No notifications.** Nothing tells anyone a story changed status; the commit is the only signal.
* **Non-technical stakeholders cannot read this** without repo access. If that becomes a
  requirement, publish `docs/` with GitHub Pages or MkDocs rather than going back to Confluence.
* **`BACKLOG.md` is a single large file** and will conflict if several people edit it at once.
  If that starts hurting, split it one file per epic.
