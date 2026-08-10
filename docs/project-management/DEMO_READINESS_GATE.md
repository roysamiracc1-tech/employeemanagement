# Demo Readiness Gate

**Owner: Senior Product Manager (verdict) · Runner: Delivery / Release Manager (checklist).**
Nothing is demonstrated to the stakeholder until this gate returns **GO**.

---

## Why this exists

On **9 August 2026** a position-change demo was shown to the stakeholder having been rehearsed only
along the path the team had built. The stakeholder asked two questions the team had not asked itself
— *"where is the rejection?"* and *"why does the bell not show this?"* — and both exposed real
defects that were live in the product:

| | Defect | Why nobody caught it |
|---|---|---|
| DEF-001 | A position change awaiting your decision never appeared in the notification bell's approvals area — it queried vacation only, so the bell read "No pending approvals ✓" while an approval sat waiting. | The workflow engine was tested. The route a user takes to *find* the work was not. |
| DEF-002 | Every notification except one event type rendered a red ❌ — an undecided request and a completed approval both read as refusals. | UAT asserted the bell *opened*. It never asserted what was *inside* it. |
| DEF-003 | "Awaiting your approval" survived in the bell after the request was decided. | No test outlived a single state transition. |

Every automated suite was green throughout. **Green suites are not a demo rehearsal.** The gate below
is what the team owes the stakeholder instead.

**The governing principle: demo the feature the way a user meets it, not the way the team built it.**
A user does not start at the happy path with the right role already selected. They arrive at a
dashboard, look for the thing that needs them, act, get it wrong, and expect the product to tell them
what happened.

---

## The rule

1. The SPM does not schedule a demo until every check below has a named owner's **evidence**, not
   their assurance.
2. Any single unchecked box is **NO-GO**. There is no "minor" exemption — DEF-002 was a single emoji.
3. The gate is run **against the state the demo will actually run in** — same database, same seeded
   users, same browser. A check that passed on a different data set has not passed.
4. Findings from the gate become backlog defects **before** the demo, not after. If a defect is
   knowingly carried into a demo, the SPM says so out loud at the start of the demo. Discovering it
   live in front of the stakeholder is a process failure, not bad luck.
5. The gate's output is recorded (template at the bottom) and lives with the story.

---

## Delegated responsibilities

The SPM owns the verdict and delegates the checks. Nobody signs off their own build.

| # | Check | Accountable | Evidence required |
|---|---|---|---|
| **D1** | **Story truth** — the demo shows what the story actually promised; acceptance criteria are restated and each is demonstrable | Business Analyst | AC list, each mapped to a demo step |
| **D2** | **Every actor, end to end** — the journey is walked as *each* role it touches: initiator, every approval level, the subject, and a bystander who must NOT see it | UAT Lead | Named user per role; screenshot per role |
| **D3** | **Both outcomes** — the unhappy path is demoed alongside the happy path: reject, cancel, expire, permission-denied, and the guard rails (duplicate, self-service, cross-tenant) | UAT Lead | Rejection/guard run recorded, with the state proven unchanged afterwards |
| **D4** | **Feedback surfaces** — for every state change, what does the user actually *see*? Notification bell, badge count, empty states, status labels, icons, colour. Each is checked for **presence, correctness and retirement** | UX / Product Designer | The blind-spot list below, ticked per surface |
| **D5** | **Access & tenancy** — feature-gated not role-hardcoded; company-scoped; the five CLAUDE.md checks pass | Senior Architect | The 5 checks, answered with the query or route that proves each |
| **D6** | **State & rehearsal** — the demo data is in a known state, the run is rehearsed end to end at least once, and it is re-runnable (a demo that only works once is not a demo) | Delivery / Release Manager | A clean rehearsal log |
| **D7** | **Automated evidence** — `pytest`, `tests/ui/test_browser.py`, `tests/ui/test_vacation_workflow.py` all 0 failures, **and** the suites actually assert the behaviour being demoed | UAT Lead | Pass counts + the specific assertions covering this story |
| **D8** | **Documentation truth** — every document the change makes false is updated in the same commit (Charter §5b) | Owner per §5b | The diff |
| **D9** | **Demo script** — a written running order: what is shown, in what order, as whom, and what the stakeholder should conclude from each step | Senior Product Manager | The script itself |

**Concurrency check (D6a).** If anything else may be writing to the demo database, say so before
starting and pick uncontended demo data. A demo that collides with another actor mid-run is
indistinguishable from a bug and burns the stakeholder's trust in everything else shown that day.

---

## D4 blind-spot list — the surfaces teams forget

Run this for **every** state change in the story. It exists because these are exactly the surfaces
that had no coverage on 9 Aug 2026.

- [ ] **Notification bell — actionable area.** Does the item requiring a decision appear *with its
      decision controls*, next to every other kind of approval? A call to action rendered as
      read-only text is a defect.
- [ ] **Badge count.** Does the number include this? A badge that stays silent about work waiting is
      work nobody does.
- [ ] **Icon / colour semantics.** Does the icon state the **outcome**? An item with no outcome yet
      must not wear one. Never let "not this one specific event" fall through to a failure icon.
- [ ] **Retirement.** Once decided, does the call to action *leave* — for **every** eligible
      approver, not just the one who acted?
- [ ] **Empty states.** When there is nothing, does the surface say so truthfully? "No pending
      approvals ✓" while an approval is pending is worse than showing nothing.
- [ ] **The other approvers.** Several people can hold an approving role. Check the one who did
      *not* act.
- [ ] **The subject.** The person the change is *about* is told what happened to them.
- [ ] **The requester.** Receipt on submit, progress on each level, outcome at the end.
- [ ] **Status vocabulary.** The same word in the list, the dialog, the notification and the
      backlog — PENDING/APPROVED/REJECTED do not become "in review" somewhere.
- [ ] **Deep links.** "View →" lands somewhere useful, and a stale link does not open a dead dialog.

---

## Sign-off record

Copy into the story's entry in [`BACKLOG.md`](BACKLOG.md) or the deliverable, filled in.

```
DEMO READINESS GATE — <story id> — <date>
Demo scope     : <what will be shown>
Data / env     : <db, users, url> · concurrent writers: <none | who>
D1 Story truth        : <owner> — <evidence>
D2 Every actor        : <owner> — <evidence>
D3 Both outcomes      : <owner> — <evidence>
D4 Feedback surfaces  : <owner> — blind-spot list <n>/10
D5 Access & tenancy   : <owner> — 5/5 CLAUDE.md checks
D6 State & rehearsal  : <owner> — rehearsed <n> times, re-runnable Y/N
D7 Automated evidence : <owner> — pytest <n>, browser <n>, vacation <n>
D8 Documentation      : <owner> — <diff>
D9 Demo script        : SPM — <link>
Known defects carried into the demo: <none | list, and stated aloud at the start>
VERDICT (SPM): GO / NO-GO
```

---

## Relationship to the other gates

This gate sits **before** a demo. It does not replace:

- **Definition of Done** (Charter §4) — what makes a story finished.
- **Production-Ready / Customer-Ready** (Charter §4) — what makes a release shippable.
- **Release Gate** (Delivery / Release Manager) — whether it ships.

A story can pass DoD and still fail this gate: DoD asks whether the work is complete, this gate asks
whether the work survives contact with a stakeholder who did not build it.
