"""Performance review cycles and eligibility — EP44 P0 (KAN-219, KAN-220).

The foundation of performance management: nothing else in the epic exists without
a round to hang it on.

Public API (used by app/routes/performance.py):
    list_cycles(company_id)                       -> list[dict]
    active_cycle(company_id)                      -> dict | None
    create_cycle(company_id, name, year, opens_on, closes_on, ..., actor)
    update_cycle(company_id, cycle_id, ..., actor)
    advance_cycle(company_id, cycle_id, to_status, actor)
    close_cycle(company_id, cycle_id, actor)
    discard_draft(company_id, cycle_id, actor)
    preview_eligibility(company_id, cycle_id)     -> dict   (changes nothing)
    take_snapshot(company_id, cycle_id, actor)    -> dict
    participants(company_id, cycle_id, ...)       -> list[dict]
    override_participation(company_id, cycle_id, employee_id, include, reason, actor)
    coverage(company_id, cycle_id)                -> dict

Every function is company-scoped. **Nothing here reads or writes pay** (AC-219-09):
a cycle is independent of the pay round, which keeps the compensation dependency
one-directional and stops a rating reaching an amount through a shared key.
"""
import datetime
import logging

from app.db import query, execute, insert_returning, to_dict, transaction
from app.services import audit_service

logger = logging.getLogger(__name__)

# Forward-only (AC-219-02). The index is the order; you may advance one or more
# steps but never go back.
CYCLE_STATES = ('DRAFT', 'OPEN', 'IN_REVIEW', 'CALIBRATION', 'CLOSED')

STATE_LABELS = {
    'DRAFT':       'Draft',
    'OPEN':        'Open — goals and milestones',
    'IN_REVIEW':   'In review — assessments',
    'CALIBRATION': 'Calibration',
    'CLOSED':      'Closed',
}

EXCLUSION_LABELS = {
    'NEW_JOINER':               'Joined too close to the end of the period',
    'LEAVER':                   'Leaving before the period ends',
    'EXCLUDED_EMPLOYMENT_TYPE': 'Employment type excluded by this round’s policy',
    'NO_MANAGER':               'No line manager — nobody to assess them',
    'HR_EXCLUDED':              'Excluded by HR',
}

DEFAULT_JOINER_CUTOFF_DAYS = 90
DEFAULT_EXCLUDED_TYPES = ['CONTRACTOR']


class CycleError(Exception):
    """A business-rule refusal carrying a message meant for the user."""


def _actor(user):
    return {'user_id': (user or {}).get('user_id'),
            'employee_id': (user or {}).get('employee_id'),
            'roles': (user or {}).get('roles') or []}


def _cycle(company_id, cycle_id, for_update=False):
    row = query("""
        SELECT id::text, name, period_year, opens_on, closes_on,
               self_assessment_deadline, joiner_cutoff_days,
               excluded_employment_types, status, opened_at, closed_at
        FROM performance_cycles
        WHERE id=%s::uuid AND company_id=%s::uuid
    """, (cycle_id, company_id), one=True)
    if not row:
        raise CycleError('That review round does not exist in this company.')
    return to_dict(row)


# ── Cycles ────────────────────────────────────────────────────────────────────

def list_cycles(company_id):
    rows = query("""
        SELECT c.id::text, c.name, c.period_year, c.opens_on, c.closes_on,
               c.self_assessment_deadline, c.status, c.opened_at, c.closed_at,
               (SELECT COUNT(*)::int FROM performance_cycle_participants p
                 WHERE p.cycle_id = c.id AND p.state = 'INCLUDED') AS included,
               (SELECT COUNT(*)::int FROM performance_cycle_participants p
                 WHERE p.cycle_id = c.id AND p.state = 'EXCLUDED') AS excluded
        FROM performance_cycles c
        WHERE c.company_id=%s::uuid
        ORDER BY c.period_year DESC
    """, (company_id,))
    out = []
    for r in rows:
        d = to_dict(r)
        d['status_label'] = STATE_LABELS.get(d['status'], d['status'])
        d['is_active'] = d['status'] != 'CLOSED'
        d['snapshot_taken'] = (d['included'] + d['excluded']) > 0
        out.append(d)
    return out


def active_cycle(company_id):
    """The one round that is not CLOSED, or None.

    Singular by construction: `uq_pc_one_active` makes two an impossibility in the
    database rather than something this function has to arbitrate.
    """
    cycles = [c for c in list_cycles(company_id) if c['is_active']]
    return cycles[0] if cycles else None


def create_cycle(company_id, name, period_year, opens_on, closes_on,
                 self_assessment_deadline=None,
                 joiner_cutoff_days=None, excluded_employment_types=None,
                 actor=None):
    """Open a DRAFT round.

    No `period_type` argument, on purpose (D-009(1)): a cycle is annual, and a
    parameter with one legal value would be a lie about what the product supports.
    """
    name = (name or '').strip()
    if not name:
        raise CycleError('Give the round a name — people will see it.')
    opens_on, closes_on = _as_date(opens_on), _as_date(closes_on)
    if not opens_on or not closes_on:
        raise CycleError('A round needs a start and an end date.')
    if closes_on <= opens_on:
        raise CycleError('The round has to end after it starts.')

    deadline = _as_date(self_assessment_deadline)
    if deadline and not (opens_on <= deadline < closes_on):
        raise CycleError('The self-assessment deadline has to fall inside the round. '
                         'A deadline after it closes is not a deadline.')

    existing = active_cycle(company_id)
    if existing:
        # Refused here with a sentence rather than letting the unique index throw
        # a constraint violation at the user.
        raise CycleError(
            f"“{existing['name']}” is still open ({existing['status_label']}). "
            f"Only one round can be running at a time — close that one first.")

    cutoff = DEFAULT_JOINER_CUTOFF_DAYS if joiner_cutoff_days is None else int(joiner_cutoff_days)
    if not 0 <= cutoff <= 365:
        raise CycleError('The joiner cut-off must be between 0 and 365 days.')
    excluded = list(excluded_employment_types) if excluded_employment_types is not None \
        else list(DEFAULT_EXCLUDED_TYPES)

    with transaction():
        row = insert_returning("""
            INSERT INTO performance_cycles
              (company_id, name, period_year, opens_on, closes_on,
               self_assessment_deadline, joiner_cutoff_days,
               excluded_employment_types, status, created_by_user_id)
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, 'DRAFT', %s::uuid)
            RETURNING id::text
        """, (company_id, name, int(period_year), opens_on, closes_on, deadline,
              cutoff, excluded, (actor or {}).get('user_id')))
        audit_service.record(
            'PERFORMANCE_CYCLE_CREATED', 'performance_cycle', row['id'],
            company_id=company_id, actor=_actor(actor),
            reason=f'Review round "{name}" created for {period_year} as a draft.',
            metadata={'period_year': int(period_year),
                      'opens_on': opens_on.isoformat(),
                      'closes_on': closes_on.isoformat(),
                      'joiner_cutoff_days': cutoff,
                      'excluded_employment_types': excluded},
            retention_class='EMPLOYMENT')
    return row['id']


def update_cycle(company_id, cycle_id, actor=None, **fields):
    """Edit a round. Most of it is only editable while it is a DRAFT."""
    before = _cycle(company_id, cycle_id)
    if before['status'] == 'CLOSED':
        raise CycleError('A closed round cannot be edited. Records point at it, so '
                         'changing it would change what they mean.')

    sets, params, changed = [], [], {}
    if 'name' in fields and fields['name'] is not None:
        if not str(fields['name']).strip():
            raise CycleError('A round needs a name.')
        sets.append('name = %s'); params.append(str(fields['name']).strip())
        changed['name'] = str(fields['name']).strip()

    if 'self_assessment_deadline' in fields:
        d = _as_date(fields['self_assessment_deadline'])
        if d and not (_as_date(before['opens_on']) <= d < _as_date(before['closes_on'])):
            raise CycleError('The self-assessment deadline has to fall inside the round.')
        sets.append('self_assessment_deadline = %s'); params.append(d)
        changed['self_assessment_deadline'] = d.isoformat() if d else None

    # Dates and policy are DRAFT-only: moving the window or the eligibility rules
    # after people have been placed in the round would silently change who should
    # have been in it.
    for key, col in (('opens_on', 'opens_on'), ('closes_on', 'closes_on')):
        if key in fields and fields[key] is not None:
            if before['status'] != 'DRAFT':
                raise CycleError('The dates can only be changed while the round is a '
                                 'draft — moving them afterwards would change who '
                                 'should have been in it.')
            sets.append(f'{col} = %s'); params.append(_as_date(fields[key]))
            changed[key] = str(fields[key])
    for key in ('joiner_cutoff_days', 'excluded_employment_types'):
        if key in fields and fields[key] is not None:
            if before['status'] != 'DRAFT':
                raise CycleError('The eligibility rules can only be changed while the '
                                 'round is a draft. This round records the policy it '
                                 'ran under, so it stays explicable later.')
            sets.append(f'{key} = %s')
            params.append(int(fields[key]) if key == 'joiner_cutoff_days'
                          else list(fields[key]))
            changed[key] = fields[key]

    if not sets:
        return
    with transaction():
        execute(f"UPDATE performance_cycles SET {', '.join(sets)} "
                f"WHERE id=%s::uuid AND company_id=%s::uuid",
                tuple(params) + (cycle_id, company_id))
        audit_service.record(
            'PERFORMANCE_CYCLE_UPDATED', 'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            reason=f'Review round "{before["name"]}" updated.',
            metadata={'status': before['status'], 'changed': changed},
            retention_class='EMPLOYMENT')


def advance_cycle(company_id, cycle_id, to_status, actor=None):
    """Move a round forward. **Forward only** (AC-219-02).

    A round is a container that assessments, calibration outcomes and step changes
    point at. Moving it backwards would silently change what those records mean —
    the same reasoning that makes a job level's ordinal immutable once occupied.
    """
    before = _cycle(company_id, cycle_id)
    if to_status not in CYCLE_STATES:
        raise CycleError('That is not a stage of a review round.')
    if to_status == 'CLOSED':
        return close_cycle(company_id, cycle_id, actor=actor)

    here, there = CYCLE_STATES.index(before['status']), CYCLE_STATES.index(to_status)
    if before['status'] == 'CLOSED':
        raise CycleError('A closed round cannot be reopened. Assessments and '
                         'decisions point at it. Open a new round instead.')
    if there <= here:
        raise CycleError(
            f'A round only moves forward. It is already at '
            f'"{STATE_LABELS[before["status"]]}".')

    # ── Entry conditions ────────────────────────────────────────────────────
    if to_status == 'OPEN':
        # AC-220-06: somebody with no manager BLOCKS the round, rather than being
        # a footnote — there is nobody to assess them, so opening anyway
        # guarantees an incomplete round.
        prev = preview_eligibility(company_id, cycle_id)
        if prev['blockers']:
            names = ', '.join(b['name'] for b in prev['blockers'][:5])
            more = '' if len(prev['blockers']) <= 5 else f' and {len(prev["blockers"]) - 5} more'
            raise CycleError(
                f"{len(prev['blockers'])} "
                f"{'person has' if len(prev['blockers']) == 1 else 'people have'} no "
                f"line manager, so nobody can assess them: {names}{more}. Give them a "
                f"manager, or exclude them deliberately, then open the round.")

    if to_status == 'IN_REVIEW':
        # AC-219-11 / OQ-10: assessments cannot start without a deadline, because
        # the deadline is the only thing that stops a silent employee deadlocking
        # their own review.
        if not before['self_assessment_deadline']:
            raise CycleError('Set the self-assessment deadline before assessments '
                             'start — it is what stops a review stalling if somebody '
                             'never submits.')
        if not _snapshot_exists(cycle_id):
            raise CycleError('Take the participant snapshot before assessments start, '
                             'so everybody knows who is in the round.')

    with transaction():
        execute("""
            UPDATE performance_cycles
            SET status = %s, opened_at = CASE WHEN %s = 'OPEN' AND opened_at IS NULL
                                              THEN NOW() ELSE opened_at END
            WHERE id=%s::uuid AND company_id=%s::uuid
        """, (to_status, to_status, cycle_id, company_id))
        audit_service.record(
            'PERFORMANCE_CYCLE_ADVANCED', 'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f'Review round "{before["name"]}" moved from '
                    f'{STATE_LABELS[before["status"]]} to {STATE_LABELS[to_status]}.'),
            metadata={'from_status': before['status'], 'to_status': to_status},
            retention_class='EMPLOYMENT')

    # The snapshot is taken ON OPENING (AC-220-01) — after the transition commits,
    # so a snapshot failure cannot leave the round in a half-opened state.
    if to_status == 'OPEN' and not _snapshot_exists(cycle_id):
        take_snapshot(company_id, cycle_id, actor=actor)
    return {'status': to_status}


def close_cycle(company_id, cycle_id, actor=None):
    """Close a round. **Irreversible** (AC-219-05)."""
    before = _cycle(company_id, cycle_id)
    if before['status'] == 'CLOSED':
        return {'status': 'CLOSED', 'already': True}
    if before['status'] == 'DRAFT':
        raise CycleError('A draft round has not run. Discard it instead of closing it '
                         '— closing implies it happened.')
    with transaction():
        execute("""
            UPDATE performance_cycles SET status='CLOSED', closed_at=NOW()
            WHERE id=%s::uuid AND company_id=%s::uuid
        """, (cycle_id, company_id))
        audit_service.record(
            'PERFORMANCE_CYCLE_CLOSED', 'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f'Review round "{before["name"]}" closed from '
                    f'{STATE_LABELS[before["status"]]}. A closed round cannot be '
                    f'reopened; a correction is an amendment.'),
            metadata={'from_status': before['status']},
            retention_class='EMPLOYMENT')
    return {'status': 'CLOSED', 'already': False}


def discard_draft(company_id, cycle_id, actor=None):
    """Delete a round that has never run. **Only a DRAFT** (AC-219-08)."""
    before = _cycle(company_id, cycle_id)
    if before['status'] != 'DRAFT':
        raise CycleError('Only a draft can be discarded. A round that has run is a '
                         'record — close it instead.')
    with transaction():
        audit_service.record(
            'PERFORMANCE_CYCLE_DISCARDED', 'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            reason=f'Draft review round "{before["name"]}" discarded before it ran.',
            metadata={'period_year': before['period_year']},
            retention_class='EMPLOYMENT')
        execute("DELETE FROM performance_cycles WHERE id=%s::uuid AND company_id=%s::uuid",
                (cycle_id, company_id))


# ── Eligibility ───────────────────────────────────────────────────────────────

def _snapshot_exists(cycle_id):
    row = query("SELECT 1 FROM performance_cycle_participants WHERE cycle_id=%s::uuid LIMIT 1",
                (cycle_id,), one=True)
    return row is not None


def _evaluate(company_id, cycle):
    """Decide, for every ACTIVE employee, whether they are in — and WHY NOT.

    Pure: reads employees and the cycle's own recorded policy and returns a
    decision per person. Writes nothing, so the preview and the snapshot cannot
    disagree about who would be included.

    **Every exclusion carries a named reason** (AC-220-02). A silent exclusion from
    a review round is the defect this story exists to prevent, and it is exactly
    what somebody would later be asked to justify.
    """
    opens_on, closes_on = _as_date(cycle['opens_on']), _as_date(cycle['closes_on'])
    cutoff_date = closes_on - datetime.timedelta(days=cycle['joiner_cutoff_days'] or 0)
    excluded_types = set(cycle['excluded_employment_types'] or [])

    rows = query("""
        SELECT e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS name,
               COALESCE(NULLIF(btrim(e.job_title), ''), '') AS job_title,
               e.join_date, e.exit_date, e.employment_type,
               mr.manager_id::text AS manager_employee_id
        FROM employees e
        LEFT JOIN manager_relationships mr
               ON mr.employee_id = e.id
              AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
        WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
        ORDER BY e.last_name, e.first_name
    """, (company_id,))

    decided = []
    for r in rows:
        d = to_dict(r)
        join_date, exit_date = _as_date(d['join_date']), _as_date(d['exit_date'])
        reason, partial = None, False

        # Order matters: the FIRST applicable reason is the one recorded, and it is
        # ordered most-specific-first so "no manager" is never masked by a
        # policy exclusion the user could have changed.
        if d['employment_type'] and d['employment_type'] in excluded_types:
            reason = 'EXCLUDED_EMPLOYMENT_TYPE'
        elif exit_date and exit_date < closes_on:
            # AC-220-04. Excluded, but anything already written about them is
            # RETAINED — an assessment is a record of a conversation that
            # happened, not a work item to tidy away.
            reason = 'LEAVER'
        elif join_date and join_date > cutoff_date:
            reason = 'NEW_JOINER'
        elif not d['manager_employee_id']:
            reason = 'NO_MANAGER'
        elif join_date and join_date > opens_on:
            # In, but on a shorter period — flagged so the manager knows they are
            # assessing less than a full year (AC-220-05).
            partial = True

        decided.append({
            'employee_id': d['employee_id'], 'name': d['name'],
            'job_title': d['job_title'],
            'manager_employee_id': d['manager_employee_id'],
            'state': 'EXCLUDED' if reason else 'INCLUDED',
            'exclusion_reason': reason,
            'exclusion_label': EXCLUSION_LABELS.get(reason),
            'is_partial': partial,
        })
    return decided


def preview_eligibility(company_id, cycle_id):
    """Who WOULD be in the round. **Changes nothing.**

    Shown before opening, because opening takes the snapshot and the snapshot is
    what every manager's list is built from — this touches everybody at once.
    """
    cycle = _cycle(company_id, cycle_id)
    decided = _evaluate(company_id, cycle)
    included = [d for d in decided if d['state'] == 'INCLUDED']
    excluded = [d for d in decided if d['state'] == 'EXCLUDED']
    # `NO_MANAGER` is the only exclusion that BLOCKS: the others are deliberate
    # policy, whereas this one means the round cannot be completed.
    blockers = [d for d in excluded if d['exclusion_reason'] == 'NO_MANAGER']
    by_reason = {}
    for d in excluded:
        by_reason.setdefault(d['exclusion_reason'], []).append(d)
    return {
        'cycle': cycle,
        'total': len(decided),
        'included': included,
        'excluded': excluded,
        'excluded_by_reason': [
            {'reason': k, 'label': EXCLUSION_LABELS.get(k), 'count': len(v),
             'people': [{'employee_id': p['employee_id'], 'name': p['name']} for p in v]}
            for k, v in sorted(by_reason.items())],
        'partial_count': sum(1 for d in included if d['is_partial']),
        'blockers': [{'employee_id': b['employee_id'], 'name': b['name']} for b in blockers],
    }


def take_snapshot(company_id, cycle_id, actor=None, re_evaluate=False):
    """Freeze who is in the round. **This is the snapshot, not a live query.**

    AC-220-01, and the load-bearing decision in KAN-220. If participation were
    resolved live: a mid-cycle joiner would silently appear in a manager's list, a
    leaver would silently vanish, and the completion meter would move for reasons
    nobody did — indistinguishable from a bug.

    Re-evaluating is therefore an **explicit action that REPORTS WHAT CHANGED**,
    and it never disturbs an HR override: HR decided that deliberately, and a
    re-run must not quietly undo it.
    """
    cycle = _cycle(company_id, cycle_id)
    if cycle['status'] == 'CLOSED':
        raise CycleError('A closed round cannot be re-snapshotted.')
    existing_rows = query("""
        SELECT employee_id::text AS employee_id, state, exclusion_reason,
               overridden_by_user_id::text AS overridden_by_user_id
        FROM performance_cycle_participants WHERE cycle_id=%s::uuid
    """, (cycle_id,))
    existing = {to_dict(r)['employee_id']: to_dict(r) for r in existing_rows}
    if existing and not re_evaluate:
        raise CycleError('This round already has a participant list. Re-evaluate it '
                         'explicitly if people have joined or left.')

    decided = _evaluate(company_id, cycle)
    added, removed, changed, kept_overrides = [], [], [], []

    with transaction():
        seen = set()
        for d in decided:
            seen.add(d['employee_id'])
            prev = existing.get(d['employee_id'])
            if prev and prev['overridden_by_user_id']:
                # ⚠ An HR override survives a re-evaluation untouched. HR made that
                # decision on purpose and a bulk re-run must not silently reverse it.
                kept_overrides.append(d['name'])
                continue
            if prev is None:
                added.append(d['name'])
            elif (prev['state'], prev['exclusion_reason']) != (d['state'], d['exclusion_reason']):
                changed.append(f"{d['name']}: {prev['state']} → {d['state']}")
            execute("""
                INSERT INTO performance_cycle_participants
                  (cycle_id, company_id, employee_id, state, exclusion_reason,
                   is_partial, manager_employee_id, snapshot_at)
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s::uuid, NOW())
                ON CONFLICT (cycle_id, employee_id) DO UPDATE
                  SET state = EXCLUDED.state,
                      exclusion_reason = EXCLUDED.exclusion_reason,
                      is_partial = EXCLUDED.is_partial,
                      manager_employee_id = EXCLUDED.manager_employee_id,
                      snapshot_at = NOW()
            """, (cycle_id, company_id, d['employee_id'], d['state'],
                  d['exclusion_reason'], d['is_partial'], d['manager_employee_id']))

        # Somebody who has left the company entirely: removed from the list, but
        # their row is kept if HR had touched it, for the same reason as above.
        for emp_id, prev in existing.items():
            if emp_id in seen or prev['overridden_by_user_id']:
                continue
            removed.append(emp_id)
            execute("DELETE FROM performance_cycle_participants "
                    "WHERE cycle_id=%s::uuid AND employee_id=%s::uuid",
                    (cycle_id, emp_id))

        # ONE audit row carrying counts, not one per person (ADR-009 §3.5): 147
        # rows saying "somebody was included" buries the rows anybody needs.
        audit_service.record(
            'PERFORMANCE_PARTICIPANTS_SNAPSHOT' if not existing
            else 'PERFORMANCE_PARTICIPANTS_RE_EVALUATED',
            'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f'Participant list {"taken" if not existing else "re-evaluated"} '
                    f'for "{cycle["name"]}": '
                    f'{sum(1 for d in decided if d["state"] == "INCLUDED")} in, '
                    f'{sum(1 for d in decided if d["state"] == "EXCLUDED")} excluded'
                    + (f'; {len(added)} added, {len(removed)} removed, '
                       f'{len(changed)} changed, {len(kept_overrides)} HR overrides kept'
                       if existing else '') + '.'),
            metadata={'included': sum(1 for d in decided if d['state'] == 'INCLUDED'),
                      'excluded': sum(1 for d in decided if d['state'] == 'EXCLUDED'),
                      'added': len(added), 'removed': len(removed),
                      'changed': len(changed), 'overrides_kept': len(kept_overrides)},
            retention_class='EMPLOYMENT')

    return {'added': added, 'removed': removed, 'changed': changed,
            'overrides_kept': kept_overrides}


def participants(company_id, cycle_id, manager_employee_id=None, state=None):
    """The frozen list. Row-scopable to one manager's reports (AC-220-11)."""
    clauses = ['p.cycle_id=%s::uuid', 'p.company_id=%s::uuid']
    params = [cycle_id, company_id]
    if manager_employee_id:
        clauses.append('p.manager_employee_id=%s::uuid'); params.append(manager_employee_id)
    if state:
        clauses.append('p.state=%s'); params.append(state)
    rows = query(f"""
        SELECT p.employee_id::text AS employee_id, p.state, p.exclusion_reason,
               p.is_partial, p.override_reason, p.snapshot_at,
               p.manager_employee_id::text AS manager_employee_id,
               e.first_name || ' ' || e.last_name AS name,
               COALESCE(NULLIF(btrim(e.job_title), ''), '') AS job_title,
               m.first_name || ' ' || m.last_name AS manager_name,
               (p.overridden_by_user_id IS NOT NULL) AS is_override
        FROM performance_cycle_participants p
        JOIN employees e ON e.id = p.employee_id
        LEFT JOIN employees m ON m.id = p.manager_employee_id
        WHERE {' AND '.join(clauses)}
        ORDER BY p.state, e.last_name, e.first_name
    """, tuple(params))
    out = []
    for r in rows:
        d = to_dict(r)
        d['exclusion_label'] = EXCLUSION_LABELS.get(d['exclusion_reason'])
        out.append(d)
    return out


def override_participation(company_id, cycle_id, employee_id, include,
                           reason=None, actor=None):
    """HR includes or excludes one person. **The reason is mandatory** (AC-220-09).

    An unexplained exclusion from a review round is exactly what a works council
    or a tribunal asks about, so the reason is the record — not a nicety.
    """
    reason = (reason or '').strip()
    if not reason:
        raise CycleError('An override needs a reason: you are setting aside the '
                         'round’s own eligibility rule for one person.')
    cycle = _cycle(company_id, cycle_id)
    if cycle['status'] == 'CLOSED':
        raise CycleError('A closed round cannot be changed.')

    row = query("""
        SELECT state, exclusion_reason FROM performance_cycle_participants
        WHERE cycle_id=%s::uuid AND employee_id=%s::uuid
    """, (cycle_id, employee_id), one=True)
    before = to_dict(row) if row else None

    mgr = query("""
        SELECT manager_id::text AS m FROM manager_relationships
        WHERE employee_id=%s::uuid AND relationship_type='SOLID_LINE' AND is_current
    """, (employee_id,), one=True)
    mgr_id = (to_dict(mgr) if mgr else {}).get('m')

    with transaction():
        execute("""
            INSERT INTO performance_cycle_participants
              (cycle_id, company_id, employee_id, state, exclusion_reason,
               manager_employee_id, overridden_by_user_id, override_reason, snapshot_at)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s::uuid, %s::uuid, %s, NOW())
            ON CONFLICT (cycle_id, employee_id) DO UPDATE
              SET state = EXCLUDED.state,
                  exclusion_reason = EXCLUDED.exclusion_reason,
                  overridden_by_user_id = EXCLUDED.overridden_by_user_id,
                  override_reason = EXCLUDED.override_reason,
                  snapshot_at = NOW()
        """, (cycle_id, company_id, employee_id,
              'INCLUDED' if include else 'EXCLUDED',
              None if include else 'HR_EXCLUDED',
              mgr_id, (actor or {}).get('user_id'), reason))
        audit_service.record(
            'PERFORMANCE_PARTICIPATION_OVERRIDDEN', 'performance_cycle', cycle_id,
            company_id=company_id, actor=_actor(actor),
            subject_employee_id=employee_id,
            reason=(f'HR {"included" if include else "excluded"} this employee in '
                    f'"{cycle["name"]}", overriding the round’s rule. Reason: {reason}'),
            metadata={'include': bool(include),
                      'state_before': (before or {}).get('state'),
                      'reason_before': (before or {}).get('exclusion_reason')},
            retention_class='EMPLOYMENT')


def coverage(company_id, cycle_id):
    """A named figure with its denominator, and the excluded LISTED (AC-220-10).

    Never a bare percentage: the excluded are the actionable part, and a
    percentage without its remainder hides exactly the people somebody would be
    asked about.
    """
    rows = participants(company_id, cycle_id)
    included = [r for r in rows if r['state'] == 'INCLUDED']
    excluded = [r for r in rows if r['state'] == 'EXCLUDED']
    by_reason = {}
    for r in excluded:
        by_reason.setdefault(r['exclusion_reason'], []).append(r['name'])
    return {
        'total': len(rows),
        'included': len(included),
        'excluded': len(excluded),
        'partial': sum(1 for r in included if r['is_partial']),
        'overrides': sum(1 for r in rows if r['is_override']),
        'pct': round(len(included) * 100.0 / len(rows), 1) if rows else None,
        'excluded_by_reason': [
            {'reason': k, 'label': EXCLUSION_LABELS.get(k), 'count': len(v), 'names': v}
            for k, v in sorted(by_reason.items())],
    }


def _as_date(v):
    from app.helpers import as_date
    return as_date(v)
