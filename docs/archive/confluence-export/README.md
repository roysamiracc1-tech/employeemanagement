# Confluence Export — 8 August 2026

Frozen, verbatim snapshots of every page that existed in the Atlassian Confluence site
`roysamiracc1-1777144763345.atlassian.net` at the time the project moved its documentation into git.

**These files are historical records. Do not edit them and do not treat them as current.**
The living documentation is in [`docs/`](../../) — see
[`docs/project-management/README.md`](../project-management/README.md) for where each topic now lives.

## What was in Confluence

The site had three spaces. Only five pages contained real content; everything else was
unmodified Atlassian starter/template boilerplate and was not exported.

### Space `EmployeeMa` — "EmployeeManagement"

| Confluence page | Last edited | Exported to | Status |
| --- | --- | --- | --- |
| HR Portal — Business Overview, Features & Access Rights | 18 May 2026 | *(promoted)* [`docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`](../../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md) | **Unique content** — had no local equivalent, so it became a living doc rather than an archive copy |
| HR Portal — Business Documentation | 26 Apr 2026 | [`business-documentation.md`](business-documentation.md) | Superseded by [`docs/BUSINESS_DOCUMENTATION.md`](../../BUSINESS_DOCUMENTATION.md) |
| HR Portal — Technical Documentation | 18 May 2026 | [`technical-documentation.md`](technical-documentation.md) | Superseded by [`docs/TECHNICAL_DOCUMENTATION.md`](../../TECHNICAL_DOCUMENTATION.md) (10 sections vs 22) |
| HR Portal — Jira Epics & User Stories | 26 Apr 2026 | [`jira-epics-and-user-stories.md`](jira-epics-and-user-stories.md) | Superseded by [`docs/project-management/BACKLOG.md`](../project-management/BACKLOG.md) (16 epics vs 34) |
| Space home + 2 Atlassian templates | — | not exported | Boilerplate |

### Space `SD` — "Software Development"

| Confluence page | Exported to | Status |
| --- | --- | --- |
| 🏓 Office Table Tennis Tournament — Planning & Details | [`office-table-tennis-tournament.md`](office-table-tennis-tournament.md) | **Unrelated to this project.** Exported only so nothing is lost on account closure — safe to delete. |
| Space home + 3 Atlassian templates | not exported | Boilerplate |

### Space `~63d7caad86a66a7cc7a4ec8c` — personal

Entirely Atlassian onboarding boilerplate ("Overview", "Getting started in Confluence from Jira").
Nothing exported.

## What was in Jira

**Nothing.** The `KAN` project ("My Kanban Space") existed but contained **zero issues** when this
export was taken — every `KAN-###` key referenced across the documentation was already a dead link.
The 16-epic / 80-story structure described in the exported Confluence page, and the 34-epic structure
in the local backlog, survive only as markdown. They were not recoverable from Jira.

## Fidelity notes

* Exported through the Atlassian MCP API in `markdown` content format.
* Confluence-specific constructs (status lozenges, smart links, `<custom>` nodes, embedded media
  blobs) do not survive that conversion. The pages exported here contained none of significance.
* Page metadata (version history, comments, inline comments, restrictions) was **not** exported.
  If any of that matters, retrieve it before closing the Atlassian account.
