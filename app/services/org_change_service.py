"""Org-change (position change) workflow engine.

A manager / HR / portal admin proposes moving an employee to a new business unit,
functional unit, location and/or reporting manager. The proposal flows through a
company-configurable, multi-level, SEQUENTIAL approval chain before it is applied.

Public API (used by app/routes/org_change.py):
    workflow_steps(company_id)                         -> list[step dict]
    create_request(company_id, subject_id, requester_user_id, proposed, reason) -> request_id
    decide(request_id, user, decision, note)           -> new status
    cancel(request_id, user)                            -> None
    list_pending(user)                                  -> list[row]
    list_my_requests(user)                              -> list[row]
    request_detail(request_id)                          -> dict

`user` is a light dict: {'user_id', 'employee_id', 'roles' (list), 'company_id'}.
"""
import datetime
import logging

from app.db import query, execute, insert_returning, to_dict, transaction
from app.helpers import as_date
from app.services import audit_service
from app.services import notification_service as notif

logger = logging.getLogger(__name__)

# Default chain when a company has not configured one: a single HR approval step.
_DEFAULT_STEPS = [
    {'step_order': 1, 'approver_type': 'ROLE', 'approver_role': 'HR_ADMIN',
     'approver_employee_id': None, 'label': 'HR approval'},
]

# ── Effective dating (KAN-189 · ADR-020) ──────────────────────────────────────
#
# HALF-OPEN INTERVALS, `[effective_from, effective_to)`, PROJECT-WIDE.
# `effective_to` is the first day the row does NOT cover — the day the next row
# starts. So one date closes the outgoing row and opens the incoming one, and the
# two physically cannot disagree about the boundary.
#
# This is what closes CFL-4 **with no history rewritten**. The old code closed an
# assignment with `effective_to = CURRENT_DATE` and let the new row default
# `effective_from` to CURRENT_DATE too. Read as inclusive `[from, to]` that is a
# one-day overlap — both rows claim today — and the fix would have meant
# rewriting every historical row. Read as half-open it is already correct and
# gapless. The defect was the *absence of a stated convention*, not the data.
#
# The visible consequence: a period ending 31 March STORES 2026-04-01. Never
# render `effective_to` raw — use `fmt_period()` in app/helpers.py, which
# subtracts the day. A test greps templates to enforce it.

# The company-configurable window. D1 puts these on `company_compensation_settings`
# (technical design §3.4) — a W1/W2 table that does not exist yet, and creating a
# stub of it here would be worse than waiting: that table is created with
# `IF NOT EXISTS`, so a partial early version would make W1's migration silently
# skip and leave the rest of its columns missing. That is the CI-drift trap in
# CLAUDE.md, not a hypothetical.
#
# So the defaults are the documented ones, and `_dating_window()` is the SINGLE
# place that changes when the table lands: it starts returning the company's row
# and every caller is already asking per-company. Per-company configurability is
# therefore NOT yet delivered — see BACKLOG.md KAN-189 for that being stated
# plainly rather than implied.
_BACKDATE_LIMIT_DAYS     = 90
_FORWARD_DATE_LIMIT_DAYS = 180

# Request types whose effect is a PLACEMENT — where somebody physically reports
# or sits. These can never be future-dated: there is no scheduler to wake up and
# apply them (EP38 R5.6 / S16), so a future date would silently become "applied
# the moment the last approver clicked", which is precisely the lie the effective
# date exists to stop. A future-dated PAY record is inert data until its date and
# every read filters on the date, so that case is permitted — hence the asymmetry.
_PLACEMENT_REQUEST_TYPES = frozenset({'TRANSFER', 'LEVEL_CHANGE'})


def _dating_window(company_id):
    """(backdate_limit_days, forward_date_limit_days) for *company_id*.

    Company-scoped by signature from day one, so the switch to the real settings
    table is a change inside this function and nowhere else.
    """
    return _BACKDATE_LIMIT_DAYS, _FORWARD_DATE_LIMIT_DAYS


def _validate_effective_date(company_id, eff, request_type='TRANSFER'):
    """Return None if *eff* is allowed, else a human error naming the reason.

    Returns a message rather than raising: every caller is a route that owes the
    user a specific 400, and the reason is the whole value of the check.
    """
    if eff is None:
        return None                          # means "apply on approval" (pre-KAN-189)
    if not isinstance(eff, datetime.date):
        return 'The effective date is not a valid date.'
    today = datetime.date.today()
    back, fwd = _dating_window(company_id)

    if eff > today and request_type in _PLACEMENT_REQUEST_TYPES:
        # Named, not generic: an HR user who picked next Monday needs to know the
        # move is not queued for next Monday, because they would otherwise assume
        # it was and stop watching for it.
        return ('A move cannot be dated in the future — there is nothing to apply '
                'it on the day. Raise it on or before the day it takes effect.')
    if eff < today - datetime.timedelta(days=back):
        return (f'That date is more than {back} days ago. '
                f'Backdating is limited to {back} days.')
    if eff > today + datetime.timedelta(days=fwd):
        return (f'That date is more than {fwd} days ahead. '
                f'Forward dating is limited to {fwd} days.')
    return None


# ── Workflow config ───────────────────────────────────────────────────────────

def workflow_steps(company_id):
    """Ordered steps for a company. Falls back to a single HR_ADMIN step."""
    wf = query(
        "SELECT id::text FROM org_change_workflows WHERE company_id=%s::uuid AND is_active",
        (company_id,), one=True)
    if not wf:
        return list(_DEFAULT_STEPS)
    steps = [to_dict(r) for r in query("""
        SELECT step_order, approver_type, approver_role,
               approver_employee_id::text AS approver_employee_id, label
        FROM org_change_workflow_steps
        WHERE workflow_id=%s::uuid ORDER BY step_order
    """, (wf['id'],))]
    return steps or list(_DEFAULT_STEPS)


def save_workflow(company_id, name, steps):
    """Replace-all: (re)create the company's chain and its ordered steps."""
    wf = query("SELECT id::text FROM org_change_workflows WHERE company_id=%s::uuid",
               (company_id,), one=True)

    # ADR-006: replace-all is one unit of work. A failure part-way through the step
    # loop must not leave the company with its old chain deleted and a partial new
    # one — that would silently change who can approve a position change.
    with transaction():
        if wf:
            wf_id = wf['id']
            execute("UPDATE org_change_workflows SET name=%s, is_active=TRUE WHERE id=%s::uuid",
                    (name or 'Position Change Approval', wf_id))
            execute("DELETE FROM org_change_workflow_steps WHERE workflow_id=%s::uuid", (wf_id,))
        else:
            wf_id = insert_returning(
                "INSERT INTO org_change_workflows (company_id, name) VALUES (%s::uuid,%s) RETURNING id::text",
                (company_id, name or 'Position Change Approval'))['id']

        for i, s in enumerate(steps, start=1):
            atype = s.get('approver_type')
            role  = (s.get('approver_role') or None) if atype == 'ROLE' else None
            emp   = (s.get('approver_employee_id') or None) if atype == 'EMPLOYEE' else None
            if atype not in ('ROLE', 'EMPLOYEE') or (atype == 'ROLE' and not role) or (atype == 'EMPLOYEE' and not emp):
                continue
            execute("""
                INSERT INTO org_change_workflow_steps
                  (workflow_id, step_order, approver_type, approver_role, approver_employee_id, label)
                VALUES (%s::uuid,%s,%s,%s,%s::uuid,%s)
            """, (wf_id, i, atype, role, emp, (s.get('label') or None)))
    return wf_id


# ── Approver resolution ───────────────────────────────────────────────────────

def _step_approver_user_ids(company_id, step, subject_employee_id=None):
    """User ids eligible to decide *step* within *company_id*.

    *subject_employee_id* is excluded (KAN-203). The subject can never decide a
    request about themselves, so putting "awaiting your approval" in their bell
    would be a call to action that is refused the moment they answer it — the
    exact DEF-001/2/3 failure mode, a control offered where it cannot work.
    Excluding them here also means the badge count never includes it.

    The argument is optional only so a step can still be resolved with no
    request in hand; every caller in this engine passes the subject.
    """
    if step['approver_type'] == 'EMPLOYEE':
        if subject_employee_id and step.get('approver_employee_id') \
                and str(step['approver_employee_id']) == str(subject_employee_id):
            return []
        row = query("SELECT id::text FROM users WHERE employee_id=%s::uuid AND is_active LIMIT 1",
                    (step['approver_employee_id'],), one=True)
        return [row['id']] if row else []
    # `IS DISTINCT FROM` rather than `<>` so a NULL subject (no exclusion asked
    # for) keeps every approver instead of silently emptying the list.
    rows = query("""
        SELECT DISTINCT u.id::text AS id
        FROM users u
        JOIN employees e ON e.id = u.employee_id AND e.company_id = %s::uuid
                        AND e.employment_status = 'ACTIVE'
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id AND r.name = %s
        WHERE u.is_active
          AND u.employee_id IS DISTINCT FROM %s::uuid
    """, (company_id, step['approver_role'], subject_employee_id))
    return [r['id'] for r in rows]


def _user_matches_step(user, step):
    """Is *user* allowed to decide *step*?"""
    if step['approver_type'] == 'EMPLOYEE':
        return user.get('employee_id') == step['approver_employee_id']
    return step['approver_role'] in (user.get('roles') or [])


# Every notification this engine writes is ABOUT one request, so it can be
# retired when that request stops being actionable (DEF-003).
_RELATED = 'ORG_CHANGE_REQUEST'
# The call-to-action event. Retiring this one clears "awaiting your approval"
# from the bell of every approver at the level just decided — including the ones
# who never opened it.
_CALL_TO_ACTION = ['ORG_CHANGE_REQUESTED']


def _notify(user_ids, event_type, message, link='/org-change', req_id=None):
    for uid in set(u for u in user_ids if u):
        notif.create_user_notification(uid, event_type, message, link=link,
                                       related_type=_RELATED if req_id else None,
                                       related_id=req_id)


def _retire_call_to_action(request_id):
    """The level just decided is closed — nobody is 'awaiting' it any more."""
    notif.resolve_related(_RELATED, request_id, _CALL_TO_ACTION)


def _emp_name(emp_id):
    r = query("SELECT first_name||' '||last_name AS n FROM employees WHERE id=%s::uuid",
              (emp_id,), one=True)
    return r['n'] if r else 'an employee'


# ── Current placement snapshot ────────────────────────────────────────────────

def current_placement(emp_id):
    """Employee's current BU/FU/location/cost-centre + solid-line manager (ids)."""
    oa = query("""
        SELECT business_unit_id::text AS bu, functional_unit_id::text AS fu,
               location_id::text AS loc, cost_center_id::text AS cc
        FROM employee_org_assignments
        WHERE employee_id=%s::uuid AND is_current
        ORDER BY effective_from DESC LIMIT 1
    """, (emp_id,), one=True)
    mgr = query("""
        SELECT manager_id::text AS mgr FROM manager_relationships
        WHERE employee_id=%s::uuid AND relationship_type='SOLID_LINE' AND is_current LIMIT 1
    """, (emp_id,), one=True)
    d = to_dict(oa) if oa else {'bu': None, 'fu': None, 'loc': None, 'cc': None}
    d['mgr'] = mgr['mgr'] if mgr else None
    return d


# ── Create ────────────────────────────────────────────────────────────────────

def create_request(company_id, subject_id, requester_user_id, proposed, reason,
                   *, effective_date=None):
    """Create a PENDING request and notify step-1 approvers + the requester.

    *effective_date* (KAN-189) defaults to today — the behaviour every request
    raised before this existed already had. Keyword-only so the four positional
    arguments keep their meaning and a future `request_type` / `compensation`
    (ADR-021) can be added beside it without re-ordering anything.

    The date is validated by the route, which owes the user the specific reason;
    it is re-checked here so the engine cannot be handed an out-of-window date by
    a second caller. Same rule as the initiator check: the route's guard is the
    message, the service's is the control.
    """
    effective_date = effective_date or datetime.date.today()
    problem = _validate_effective_date(company_id, effective_date)
    if problem:
        raise ValueError(problem)

    cur   = current_placement(subject_id)
    steps = workflow_steps(company_id)
    wf = query("SELECT id::text FROM org_change_workflows WHERE company_id=%s::uuid AND is_active",
               (company_id,), one=True)
    wf_id = wf['id'] if wf else None

    # ADR-006: the request and its full approval chain are one unit of work. A
    # request with a partial chain would be approvable in fewer levels than the
    # company configured — a silent weakening of the control.
    with transaction():
        req = insert_returning("""
            INSERT INTO org_change_requests
              (company_id, employee_id, requested_by_user_id, reason,
               from_business_unit_id, from_functional_unit_id, from_location_id, from_manager_id,
               proposed_business_unit_id, proposed_functional_unit_id, proposed_location_id, proposed_manager_id,
               workflow_id, current_step, effective_date, status)
            VALUES (%s::uuid,%s::uuid,%s::uuid,%s,
                    %s::uuid,%s::uuid,%s::uuid,%s::uuid,
                    %s::uuid,%s::uuid,%s::uuid,%s::uuid,
                    %s::uuid,1,%s,'PENDING')
            RETURNING id::text
        """, (company_id, subject_id, requester_user_id, (reason or None),
              cur['bu'], cur['fu'], cur['loc'], cur['mgr'],
              proposed.get('business_unit_id'), proposed.get('functional_unit_id'),
              proposed.get('location_id'), proposed.get('manager_id'),
              wf_id, effective_date))
        req_id = req['id']

        for s in steps:
            execute("""
                INSERT INTO org_change_approvals
                  (request_id, step_order, approver_type, approver_role, approver_employee_id)
                VALUES (%s::uuid,%s,%s,%s,%s::uuid)
            """, (req_id, s['step_order'], s['approver_type'],
                  s.get('approver_role'), s.get('approver_employee_id')))

    # Notifications are sent only after the unit of work has committed — they
    # cannot be rolled back (EP38 technical design §5.4).
    subj = _emp_name(subject_id)
    total = len(steps)
    # Notify first-step approvers. ORG_CHANGE_REQUESTED is the CALL TO ACTION —
    # it is retired the moment the level it belongs to is decided.
    _notify(_step_approver_user_ids(company_id, steps[0], subject_id), 'ORG_CHANGE_REQUESTED',
            f"Position change requested for {subj} — awaiting your approval (level 1 of {total}).",
            req_id=req_id)
    # Notify the requester. A DIFFERENT event type on purpose: this is a receipt,
    # not a call to action, so it must not be swept away when a level is decided
    # and it must not render with a decision icon (DEF-002).
    _notify([requester_user_id], 'ORG_CHANGE_SUBMITTED',
            f"Your position change request for {subj} was submitted ({total}-level approval).",
            req_id=req_id)
    return req_id


# ── Decide ────────────────────────────────────────────────────────────────────

_STEP_DECISION_SQL = """
    UPDATE org_change_approvals
    SET decision=%s, note=%s, decided_by_user_id=%s::uuid, decided_at=NOW()
    WHERE request_id=%s::uuid AND step_order=%s
"""


def _is_self_subject(user, req):
    """Is the deciding user the subject of *req*? (KAN-203)

    String comparison: the session carries `employee_id` as text, the row as a
    UUID cast to text.
    """
    emp_id = user.get('employee_id')
    return bool(emp_id and req.get('employee_id')
                and str(emp_id) == str(req['employee_id']))


def _audit_self_decision_refused(req, user):
    """Record a refused self-decision (KAN-203). Never raises into the caller.

    Opens its own transaction: a refusal has no unit of work to join. See the
    matching helper in `app/routes/org_change.py` for the reasoning.
    """
    try:
        with transaction():
            audit_service.record(
                'ORG_CHANGE_SELF_ACTION_REFUSED',
                'org_change_request', req['id'],
                company_id=req['company_id'],
                actor=user,
                subject_employee_id=req['employee_id'],
                reason='Refused: user attempted to decide a position change '
                       'about themselves (KAN-203).',
                outcome='FAILED',
                error_code='SELF_ACTION_REFUSED',
                retention_class='SECURITY',
                metadata={'attempted': 'DECIDE',
                          'step': req.get('current_step')},
            )
    except Exception:
        logger.exception('KAN-203: failed to audit refused self-decision')


def decide(request_id, user, decision, note):
    """Approve/reject the CURRENT step. Returns (ok, status_or_error)."""
    if decision not in ('approve', 'reject'):
        return False, 'action must be approve or reject'

    req = query("""
        SELECT id::text, company_id::text, employee_id::text, requested_by_user_id::text,
               current_step, status, proposed_manager_id::text AS proposed_manager_id
        FROM org_change_requests WHERE id=%s::uuid
    """, (request_id,), one=True)
    if not req:
        return False, 'not found'
    req = to_dict(req)
    if req['company_id'] != user.get('company_id') and 'SYSTEM_ADMIN' not in (user.get('roles') or []):
        return False, 'not your company'

    # KAN-203 — nobody decides a request whose SUBJECT is themselves: any level,
    # any role, SYSTEM_ADMIN included. This is an integrity control, not a
    # judgement about an amount, so it is refused outright and is deliberately
    # NOT subject to the advise-and-override rule that governs pay decisions.
    # Checked ahead of the step lookup so a subject cannot use the error message
    # to learn who is approving them.
    if _is_self_subject(user, req):
        _audit_self_decision_refused(req, user)
        return False, ('you cannot decide a position change about yourself — '
                       'another approver must decide it')

    if req['status'] != 'PENDING':
        return False, 'request is no longer pending'

    step = query("""
        SELECT step_order, approver_type, approver_role,
               approver_employee_id::text AS approver_employee_id
        FROM org_change_approvals WHERE request_id=%s::uuid AND step_order=%s
    """, (request_id, req['current_step']), one=True)
    if not step:
        return False, 'approval step missing'
    step = to_dict(step)
    if not _user_matches_step(user, step) and 'SYSTEM_ADMIN' not in (user.get('roles') or []):
        return False, 'you are not an approver for this step'

    new_dec = 'APPROVED' if decision == 'approve' else 'REJECTED'
    step_params = (new_dec, (note or None), user['user_id'], request_id, req['current_step'])

    subj = _emp_name(req['employee_id'])

    # ADR-006: recording the step decision and whatever it triggers (reject the
    # request / advance a level / apply the move and close it out) is ONE unit of
    # work. Anything else can leave a step marked decided while the request never
    # moved, or a move applied against a request still showing PENDING.
    if decision == 'reject':
        with transaction():
            execute(_STEP_DECISION_SQL, step_params)
            execute("UPDATE org_change_requests SET status='REJECTED', decided_at=NOW(), updated_at=NOW() WHERE id=%s::uuid",
                    (request_id,))
        # Retire BEFORE announcing: a rejection ends the request, so no approver
        # at any level is still "awaiting" it. Without this the other HR admins
        # keep a dead call to action in their bell for ever (DEF-003).
        _retire_call_to_action(request_id)
        msg = f"The position change for {subj} was rejected at level {req['current_step']}."
        _notify([req['requested_by_user_id']], 'ORG_CHANGE_REJECTED', msg, req_id=request_id)
        _notify(_subject_user_ids(req['employee_id']), 'ORG_CHANGE_REJECTED', msg, req_id=request_id)
        return True, 'REJECTED'

    # approve — is there a next step?
    total = query("SELECT COUNT(*)::int AS c FROM org_change_approvals WHERE request_id=%s::uuid",
                  (request_id,), one=True)['c']
    if req['current_step'] < total:
        nxt = req['current_step'] + 1
        with transaction():
            execute(_STEP_DECISION_SQL, step_params)
            execute("UPDATE org_change_requests SET current_step=%s, updated_at=NOW() WHERE id=%s::uuid",
                    (nxt, request_id))
        next_step = to_dict(query("""
            SELECT step_order, approver_type, approver_role,
                   approver_employee_id::text AS approver_employee_id
            FROM org_change_approvals WHERE request_id=%s::uuid AND step_order=%s
        """, (request_id, nxt), one=True))
        # Level N is closed. Retire its call to action for EVERY approver at that
        # level — several people can hold the approving role and only one acted —
        # then raise the call to action for level N+1 (DEF-003).
        _retire_call_to_action(request_id)
        _notify(_step_approver_user_ids(req['company_id'], next_step, req['employee_id']),
                'ORG_CHANGE_REQUESTED',
                f"Position change for {subj} — awaiting your approval (level {nxt} of {total}).",
                req_id=request_id)
        _notify([req['requested_by_user_id']], 'ORG_CHANGE_STEP_APPROVED',
                f"Your position change request for {subj} passed level {req['current_step']} — now at level {nxt} of {total}.",
                req_id=request_id)
        return True, 'PENDING'

    # final approval — apply the change. The decision, the move itself and the
    # status close-out commit together or not at all (TD-7).
    with transaction():
        execute(_STEP_DECISION_SQL, step_params)
        _apply_change(request_id)
        execute("UPDATE org_change_requests SET status='APPROVED', decided_at=NOW(), updated_at=NOW() WHERE id=%s::uuid",
                (request_id,))
    _retire_call_to_action(request_id)
    msg = f"The position change for {subj} was fully approved and applied."
    _notify([req['requested_by_user_id']], 'ORG_CHANGE_APPROVED', msg, req_id=request_id)
    _notify(_subject_user_ids(req['employee_id']), 'ORG_CHANGE_APPROVED',
            "Your position change has been approved and applied.", req_id=request_id)
    return True, 'APPROVED'


def _subject_user_ids(emp_id):
    rows = query("SELECT id::text FROM users WHERE employee_id=%s::uuid AND is_active", (emp_id,))
    return [r['id'] for r in rows]


# ── Apply ─────────────────────────────────────────────────────────────────────

def apply_change(request_id):
    """Apply the approved move atomically (standalone entry point).

    `decide()` does NOT call this — it calls `_apply_change` inside its own
    transaction, because the move and the request's status close-out are a single
    unit of work. ADR-006 forbids nesting transaction().
    """
    with transaction():
        _apply_change(request_id)


def _apply_change(request_id):
    """The statements of the move. MUST run inside an open transaction():
    closing the old assignment, opening the new one and re-pointing the manager
    are meaningless individually — a partial apply leaves an employee with no
    current org assignment or no manager."""
    r = to_dict(query("""
        SELECT employee_id::text, from_manager_id::text AS from_manager_id,
               proposed_business_unit_id::text AS bu, proposed_functional_unit_id::text AS fu,
               proposed_location_id::text AS loc, proposed_manager_id::text AS mgr,
               effective_date
        FROM org_change_requests WHERE id=%s::uuid
    """, (request_id,), one=True))
    emp_id = r['employee_id']

    # ONE boundary date for the whole move (KAN-189 · ADR-020). Falls back to
    # today for a request raised before the column existed, whose meaning was
    # always "apply on approval".
    #
    # Coerced to a real `date` because `to_dict()` serialises every DATE column to
    # an ISO string (`app/db.py serialize`). Postgres would cast the string back
    # happily, so this works either way today — but then "the same date closes and
    # opens" would be true only because two strings happen to be equal, and any
    # arithmetic added here later (a pay date offset, a proration) would break on
    # a string. The invariant should be real, not incidental.
    eff = as_date(r.get('effective_date')) or datetime.date.today()

    # Carry EVERY unchanged field forward from the outgoing current assignment.
    #
    # A proposal only stores the fields the requester actually changed; the rest
    # are NULL, which means "no change" — NOT "clear this". Inserting the raw
    # proposal therefore wiped the employee's location and functional unit
    # whenever a move touched only their business unit. The cost centre was
    # already carried this way; the other three were not, and that asymmetry was
    # the bug. Now the new row is the old row overlaid with what changed.
    old_row = query("""
        SELECT location_id::text AS loc, business_unit_id::text AS bu,
               functional_unit_id::text AS fu, cost_center_id::text AS cc
        FROM employee_org_assignments
        WHERE employee_id=%s::uuid AND is_current ORDER BY effective_from DESC LIMIT 1
    """, (emp_id,), one=True)
    # An employee may have no current assignment at all, so this must stay
    # None-safe — there is then simply nothing to carry forward.
    old = to_dict(old_row) if old_row else {}

    loc = r['loc'] or old.get('loc')
    bu  = r['bu']  or old.get('bu')
    fu  = r['fu']  or old.get('fu')
    cc  = old.get('cc')

    # The SAME `eff` closes the outgoing row and opens the incoming one. Under
    # half-open `[from, to)` that is exactly abutting: no overlapping day, no gap,
    # and no way for the two ends of the boundary to drift apart — which is what
    # made CFL-4 possible when one side was CURRENT_DATE and the other a default.
    execute("""
        UPDATE employee_org_assignments
        SET is_current=FALSE, effective_to=%s
        WHERE employee_id=%s::uuid AND is_current
    """, (eff, emp_id))
    execute("""
        INSERT INTO employee_org_assignments
          (employee_id, location_id, business_unit_id, functional_unit_id, cost_center_id,
           effective_from, is_current)
        VALUES (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s,TRUE)
    """, (emp_id, loc, bu, fu, cc, eff))

    if r['mgr'] and r['mgr'] != r['from_manager_id']:
        # DEF-42-2 — this UPDATE set `is_current=FALSE` and nothing else, so every
        # superseded reporting line was left with a NULL `effective_to`: closed,
        # but with no end date. Two such rows exist in the dev database. It reads
        # as an open-ended relationship to anything that trusts the dates instead
        # of the flag, and EP42 was about to copy this pattern into three new
        # tables. Both ends of the boundary are now explicit.
        execute("""
            UPDATE manager_relationships SET is_current=FALSE, effective_to=%s
            WHERE employee_id=%s::uuid AND relationship_type='SOLID_LINE' AND is_current
        """, (eff, emp_id))
        execute("""
            INSERT INTO manager_relationships
              (employee_id, manager_id, relationship_type, effective_from, is_current)
            VALUES (%s::uuid,%s::uuid,'SOLID_LINE',%s,TRUE)
        """, (emp_id, r['mgr'], eff))


# ── Cancel ────────────────────────────────────────────────────────────────────

def cancel(request_id, user):
    req = query("SELECT requested_by_user_id::text AS by, status, company_id::text AS company_id "
                "FROM org_change_requests WHERE id=%s::uuid", (request_id,), one=True)
    if not req:
        return False, 'not found'
    req = to_dict(req)
    is_admin = bool({'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'} & set(user.get('roles') or []))
    if req['by'] != user.get('user_id') and not is_admin:
        return False, 'not allowed'
    if req['status'] != 'PENDING':
        return False, 'only pending requests can be cancelled'
    execute("UPDATE org_change_requests SET status='CANCELLED', decided_at=NOW(), updated_at=NOW() WHERE id=%s::uuid",
            (request_id,))
    # A cancelled request is not awaiting anyone either — same reasoning as a
    # rejection (DEF-003). Approvers are not told it was cancelled (they never
    # asked for it); the dead call to action simply leaves their bell.
    _retire_call_to_action(request_id)
    return True, 'CANCELLED'


# ── Queries for the inbox ─────────────────────────────────────────────────────

_DETAIL_COLS = """
    r.id::text, r.status, r.current_step, r.reason, r.created_at, r.effective_date,
    (se.first_name||' '||se.last_name) AS employee_name, se.id::text AS employee_id,
    se.job_title,
    (rb.first_name||' '||rb.last_name) AS requested_by_name,
    fbu.name AS from_bu, tbu.name AS to_bu,
    ffu.name AS from_fu, tfu.name AS to_fu,
    fl.name  AS from_loc, tl.name AS to_loc,
    (fm.first_name||' '||fm.last_name) AS from_manager,
    (tm.first_name||' '||tm.last_name) AS to_manager,
    (SELECT COUNT(*)::int FROM org_change_approvals a WHERE a.request_id=r.id) AS total_steps
"""
_DETAIL_JOINS = """
    FROM org_change_requests r
    JOIN employees se ON se.id = r.employee_id
    JOIN users ub ON ub.id = r.requested_by_user_id
    JOIN employees rb ON rb.id = ub.employee_id
    LEFT JOIN business_units  fbu ON fbu.id = r.from_business_unit_id
    LEFT JOIN business_units  tbu ON tbu.id = r.proposed_business_unit_id
    LEFT JOIN functional_units ffu ON ffu.id = r.from_functional_unit_id
    LEFT JOIN functional_units tfu ON tfu.id = r.proposed_functional_unit_id
    LEFT JOIN locations fl ON fl.id = r.from_location_id
    LEFT JOIN locations tl ON tl.id = r.proposed_location_id
    LEFT JOIN employees fm ON fm.id = r.from_manager_id
    LEFT JOIN employees tm ON tm.id = r.proposed_manager_id
"""


def list_my_requests(user):
    rows = query(f"SELECT {_DETAIL_COLS} {_DETAIL_JOINS} "
                 f"WHERE r.requested_by_user_id=%s::uuid ORDER BY r.created_at DESC",
                 (user['user_id'],))
    return [to_dict(r) for r in rows]


def list_pending(user):
    """Requests whose CURRENT step this user may decide.

    Excludes requests whose SUBJECT is *user* (KAN-203) — they may not decide
    those, and the inbox renders Approve/Reject on everything it returns, so
    including them would put live controls in front of somebody `decide()` then
    refuses. The refusal is the control; this keeps the surface honest about it.
    """
    rows = query(f"""
        SELECT {_DETAIL_COLS},
               ca.approver_type, ca.approver_role,
               ca.approver_employee_id::text AS approver_employee_id
        {_DETAIL_JOINS}
        JOIN org_change_approvals ca ON ca.request_id=r.id AND ca.step_order=r.current_step
        WHERE r.status='PENDING' AND r.company_id=%s::uuid
        ORDER BY r.created_at
    """, (user.get('company_id'),))
    out = []
    for r in rows:
        d = to_dict(r)
        if _is_self_subject(user, d):        # KAN-203 — not your own move
            continue
        step = {'approver_type': d['approver_type'], 'approver_role': d['approver_role'],
                'approver_employee_id': d['approver_employee_id']}
        if _user_matches_step(user, step) or 'SYSTEM_ADMIN' in (user.get('roles') or []):
            out.append(d)
    return out
