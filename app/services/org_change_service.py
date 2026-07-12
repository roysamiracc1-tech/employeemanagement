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

from app.db import query, execute, insert_returning, to_dict
from app.services import notification_service as notif

# Default chain when a company has not configured one: a single HR approval step.
_DEFAULT_STEPS = [
    {'step_order': 1, 'approver_type': 'ROLE', 'approver_role': 'HR_ADMIN',
     'approver_employee_id': None, 'label': 'HR approval'},
]


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

def _step_approver_user_ids(company_id, step):
    """User ids eligible to decide *step* within *company_id*."""
    if step['approver_type'] == 'EMPLOYEE':
        row = query("SELECT id::text FROM users WHERE employee_id=%s::uuid AND is_active LIMIT 1",
                    (step['approver_employee_id'],), one=True)
        return [row['id']] if row else []
    rows = query("""
        SELECT DISTINCT u.id::text AS id
        FROM users u
        JOIN employees e ON e.id = u.employee_id AND e.company_id = %s::uuid
                        AND e.employment_status = 'ACTIVE'
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id AND r.name = %s
        WHERE u.is_active
    """, (company_id, step['approver_role']))
    return [r['id'] for r in rows]


def _user_matches_step(user, step):
    """Is *user* allowed to decide *step*?"""
    if step['approver_type'] == 'EMPLOYEE':
        return user.get('employee_id') == step['approver_employee_id']
    return step['approver_role'] in (user.get('roles') or [])


def _notify(user_ids, event_type, message, link='/org-change'):
    for uid in set(u for u in user_ids if u):
        notif.create_user_notification(uid, event_type, message, link=link)


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

def create_request(company_id, subject_id, requester_user_id, proposed, reason):
    """Create a PENDING request and notify step-1 approvers + the requester."""
    cur   = current_placement(subject_id)
    steps = workflow_steps(company_id)
    wf = query("SELECT id::text FROM org_change_workflows WHERE company_id=%s::uuid AND is_active",
               (company_id,), one=True)
    wf_id = wf['id'] if wf else None

    req = insert_returning("""
        INSERT INTO org_change_requests
          (company_id, employee_id, requested_by_user_id, reason,
           from_business_unit_id, from_functional_unit_id, from_location_id, from_manager_id,
           proposed_business_unit_id, proposed_functional_unit_id, proposed_location_id, proposed_manager_id,
           workflow_id, current_step, status)
        VALUES (%s::uuid,%s::uuid,%s::uuid,%s,
                %s::uuid,%s::uuid,%s::uuid,%s::uuid,
                %s::uuid,%s::uuid,%s::uuid,%s::uuid,
                %s::uuid,1,'PENDING')
        RETURNING id::text
    """, (company_id, subject_id, requester_user_id, (reason or None),
          cur['bu'], cur['fu'], cur['loc'], cur['mgr'],
          proposed.get('business_unit_id'), proposed.get('functional_unit_id'),
          proposed.get('location_id'), proposed.get('manager_id'),
          wf_id))
    req_id = req['id']

    for s in steps:
        execute("""
            INSERT INTO org_change_approvals
              (request_id, step_order, approver_type, approver_role, approver_employee_id)
            VALUES (%s::uuid,%s,%s,%s,%s::uuid)
        """, (req_id, s['step_order'], s['approver_type'],
              s.get('approver_role'), s.get('approver_employee_id')))

    subj = _emp_name(subject_id)
    total = len(steps)
    # Notify first-step approvers
    _notify(_step_approver_user_ids(company_id, steps[0]), 'ORG_CHANGE_REQUESTED',
            f"Position change requested for {subj} — awaiting your approval (level 1 of {total}).")
    # Notify the requester
    _notify([requester_user_id], 'ORG_CHANGE_REQUESTED',
            f"Your position change request for {subj} was submitted ({total}-level approval).")
    return req_id


# ── Decide ────────────────────────────────────────────────────────────────────

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
    execute("""
        UPDATE org_change_approvals
        SET decision=%s, note=%s, decided_by_user_id=%s::uuid, decided_at=NOW()
        WHERE request_id=%s::uuid AND step_order=%s
    """, (new_dec, (note or None), user['user_id'], request_id, req['current_step']))

    subj = _emp_name(req['employee_id'])

    if decision == 'reject':
        execute("UPDATE org_change_requests SET status='REJECTED', decided_at=NOW(), updated_at=NOW() WHERE id=%s::uuid",
                (request_id,))
        msg = f"The position change for {subj} was rejected at level {req['current_step']}."
        _notify([req['requested_by_user_id']], 'ORG_CHANGE_REJECTED', msg)
        _notify(_subject_user_ids(req['employee_id']), 'ORG_CHANGE_REJECTED', msg)
        return True, 'REJECTED'

    # approve — is there a next step?
    total = query("SELECT COUNT(*)::int AS c FROM org_change_approvals WHERE request_id=%s::uuid",
                  (request_id,), one=True)['c']
    if req['current_step'] < total:
        nxt = req['current_step'] + 1
        execute("UPDATE org_change_requests SET current_step=%s, updated_at=NOW() WHERE id=%s::uuid",
                (nxt, request_id))
        next_step = to_dict(query("""
            SELECT step_order, approver_type, approver_role,
                   approver_employee_id::text AS approver_employee_id
            FROM org_change_approvals WHERE request_id=%s::uuid AND step_order=%s
        """, (request_id, nxt), one=True))
        _notify(_step_approver_user_ids(req['company_id'], next_step), 'ORG_CHANGE_REQUESTED',
                f"Position change for {subj} — awaiting your approval (level {nxt} of {total}).")
        _notify([req['requested_by_user_id']], 'ORG_CHANGE_STEP_APPROVED',
                f"Your position change request for {subj} passed level {req['current_step']} — now at level {nxt} of {total}.")
        return True, 'PENDING'

    # final approval — apply the change
    apply_change(request_id)
    execute("UPDATE org_change_requests SET status='APPROVED', decided_at=NOW(), updated_at=NOW() WHERE id=%s::uuid",
            (request_id,))
    msg = f"The position change for {subj} was fully approved and applied."
    _notify([req['requested_by_user_id']], 'ORG_CHANGE_APPROVED', msg)
    _notify(_subject_user_ids(req['employee_id']), 'ORG_CHANGE_APPROVED',
            "Your position change has been approved and applied.")
    return True, 'APPROVED'


def _subject_user_ids(emp_id):
    rows = query("SELECT id::text FROM users WHERE employee_id=%s::uuid AND is_active", (emp_id,))
    return [r['id'] for r in rows]


# ── Apply ─────────────────────────────────────────────────────────────────────

def apply_change(request_id):
    """Apply the approved move: new current org assignment + re-point solid-line manager."""
    r = to_dict(query("""
        SELECT employee_id::text, from_manager_id::text AS from_manager_id,
               proposed_business_unit_id::text AS bu, proposed_functional_unit_id::text AS fu,
               proposed_location_id::text AS loc, proposed_manager_id::text AS mgr
        FROM org_change_requests WHERE id=%s::uuid
    """, (request_id,), one=True))
    emp_id = r['employee_id']

    # carry cost centre from the outgoing current assignment
    old = query("""
        SELECT cost_center_id::text AS cc FROM employee_org_assignments
        WHERE employee_id=%s::uuid AND is_current ORDER BY effective_from DESC LIMIT 1
    """, (emp_id,), one=True)
    cc = old['cc'] if old else None

    execute("""
        UPDATE employee_org_assignments
        SET is_current=FALSE, effective_to=CURRENT_DATE
        WHERE employee_id=%s::uuid AND is_current
    """, (emp_id,))
    execute("""
        INSERT INTO employee_org_assignments
          (employee_id, location_id, business_unit_id, functional_unit_id, cost_center_id, is_current)
        VALUES (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,TRUE)
    """, (emp_id, r['loc'], r['bu'], r['fu'], cc))

    if r['mgr'] and r['mgr'] != r['from_manager_id']:
        execute("""
            UPDATE manager_relationships SET is_current=FALSE
            WHERE employee_id=%s::uuid AND relationship_type='SOLID_LINE' AND is_current
        """, (emp_id,))
        execute("""
            INSERT INTO manager_relationships (employee_id, manager_id, relationship_type, is_current)
            VALUES (%s::uuid,%s::uuid,'SOLID_LINE',TRUE)
        """, (emp_id, r['mgr']))


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
    return True, 'CANCELLED'


# ── Queries for the inbox ─────────────────────────────────────────────────────

_DETAIL_COLS = """
    r.id::text, r.status, r.current_step, r.reason, r.created_at,
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
    """Requests whose CURRENT step this user may decide."""
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
        step = {'approver_type': d['approver_type'], 'approver_role': d['approver_role'],
                'approver_employee_id': d['approver_employee_id']}
        if _user_matches_step(user, step) or 'SYSTEM_ADMIN' in (user.get('roles') or []):
            out.append(d)
    return out
