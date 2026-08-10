"""Position-change (org-change) request + approval routes.

Two entry points, ONE engine (KAN-185 / EP38 technical design §4.3):

* the org-tree drag-and-drop, and
* the task-oriented **Transfer…** entry point on an employee's profile,

both post to `POST /api/org-change/request`, which is the only caller of
`org_change_service.create_request()`. There is deliberately no second route, no
second table and no second feature code — a transfer *is* an org change, so it
inherits the sequential approval chain, the initiator rule and the company
scoping unchanged.
"""
from flask import session, request, render_template, jsonify, redirect, url_for, flash

from app import app
from app.db import query, to_dict, transaction
from app.services import audit_service
# `require_roles` is deliberately NOT imported: hardcoded role lists are
# forbidden on these routes (CLAUDE.md org-change invariant 1). The only
# role-shaped check here is the initiator business rule in `_can_initiate_for`,
# which sits on top of the feature gate rather than replacing it.
from app.auth import login_required, require_feature_access
from app.helpers import employee_solid_manager
from app.services import org_change_service as svc

_ADMIN_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')

# Org-unit tables a proposed move may point at. Fixed literals — never user input.
_UNIT_TABLES = {
    'business_unit_id':   'business_units',
    'functional_unit_id': 'functional_units',
    'location_id':        'locations',
}

# Role names that read badly under a naive title-case.
_ROLE_WORD_OVERRIDES = {'HR': 'HR', 'IT': 'IT', 'CEO': 'CEO', 'CFO': 'CFO', 'CTO': 'CTO'}


def _user():
    """Light user context for the workflow engine."""
    return {
        'user_id':     session.get('user_id'),
        'employee_id': session.get('employee_id'),
        'company_id':  session.get('company_id') or session.get('admin_company_id') or None,
        'roles':       session.get('roles', []),
    }


# The roles that may initiate a move for anyone in the company, as opposed to
# only for their own reports. Defined once — see `can_initiate_org_change_for`
# and `can_initiate_org_change_for_anyone` for why nothing may re-list it.
_INITIATOR_ADMIN_ROLES = {'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'}


def _is_self(subject_id, u):
    """Is the acting user the SUBJECT of this request? (KAN-203)

    Compared as strings because the session carries `employee_id` as text while
    callers may pass a UUID from the database.
    """
    emp_id = u.get('employee_id')
    return bool(emp_id and subject_id and str(emp_id) == str(subject_id))


def _can_initiate_for(subject_id, u):
    """Requester must manage the subject (solid line) OR be HR/Portal/System admin
    — and may never be the subject themselves.

    CLAUDE.md org-change invariant 2. This is a **business rule on top of** the
    feature gate, not a substitute for it — the feature flag alone is not
    sufficient. Every creation path must pass through here.

    **KAN-203: the self case is refused FIRST, ahead of the admin exemption.**
    That exemption exists so HR can move *other people*; it was never intended
    to cover acting on oneself, and until KAN-203 an HR_ADMIN who is also an
    employee could raise their own move. Refusing here rather than only in the
    route means the display helpers below hide the affordance too.
    """
    if _is_self(subject_id, u):
        return False
    if _INITIATOR_ADMIN_ROLES & set(u.get('roles') or []):
        return True
    return employee_solid_manager(subject_id) == u.get('employee_id')


def _audit_self_action_refused(what, company_id, subject_id, u):
    """Record a refused self-action (KAN-203). Never raises into the caller.

    The refusal IS the event — there is no other write to join, so this opens
    its own transaction. That is the one deliberate exception to `record()`'s
    "join the caller's transaction" rule (ADR-009): a refusal has no unit of
    work to belong to, and a trail that only holds successful actions cannot
    show that somebody tried.
    """
    try:
        with transaction():
            audit_service.record(
                'ORG_CHANGE_SELF_ACTION_REFUSED',
                'org_change_request', subject_id,
                company_id=company_id,
                actor=u,
                subject_employee_id=subject_id,
                reason=f'Refused: user attempted to {what.lower()} a position '
                       f'change about themselves (KAN-203).',
                outcome='FAILED',
                error_code='SELF_ACTION_REFUSED',
                retention_class='SECURITY',
                metadata={'attempted': what},
            )
    except Exception:
        # An audit failure must not convert a refusal into a 500 — the control
        # is the refusal; the row is the record of it.
        app.logger.exception('KAN-203: failed to audit refused self-%s', what.lower())


def can_initiate_org_change_for(subject_id):
    """Public read-only view of the initiator rule, for rendering entry points.

    Any surface that shows a **Transfer…** / move affordance must hide it when
    this is False — but it is a *display* helper only: hiding a button is never
    the control. `POST /api/org-change/request` re-checks `_can_initiate_for`
    server-side on every call, so a hand-crafted request is refused regardless.
    Exposed so no caller re-implements the rule (CLAUDE.md invariant 2).
    """
    return _can_initiate_for(subject_id, _user())


def can_initiate_org_change_for_anyone():
    """May the current user initiate for ANY subject, not just their own reports?

    For surfaces that render many people at once (the directory) and cannot run
    a per-row manager lookup. Callers combine this with the row's own
    `solid_manager_id` to reproduce `_can_initiate_for` without querying — so
    the admin role set stays defined in exactly one place. Display only; the API
    re-checks `_can_initiate_for` on every request.
    """
    return bool(_INITIATOR_ADMIN_ROLES & set(_user().get('roles') or []))


def _role_label(role_name):
    """`HR_ADMIN` -> `HR Admin`, for the approval-chain line in the dialog."""
    if not role_name:
        return 'Approver'
    words = [w for w in str(role_name).split('_') if w]
    return ' '.join(_ROLE_WORD_OVERRIDES.get(w.upper(), w.capitalize()) for w in words)


def _approval_chain(company_id):
    """Ordered, human-readable approval levels for *company_id*.

    Read-only reuse of the engine's own config (`workflow_steps` already falls
    back to the single HR_ADMIN step), so the dialog can never show a chain the
    engine would not build.
    """
    if not company_id:
        return []
    chain = []
    for s in svc.workflow_steps(company_id):
        if s.get('approver_type') == 'EMPLOYEE' and s.get('approver_employee_id'):
            label = svc._emp_name(s['approver_employee_id'])
        else:
            label = _role_label(s.get('approver_role'))
        chain.append({'step_order': s.get('step_order'), 'label': label,
                      'approver_type': s.get('approver_type')})
    return chain


def _pending_request_for(subject_id):
    """The subject's oldest still-PENDING request, or None (AC-185-08)."""
    row = query("""
        SELECT id::text FROM org_change_requests
        WHERE employee_id=%s::uuid AND status='PENDING'
        ORDER BY created_at LIMIT 1
    """, (subject_id,), one=True)
    return row['id'] if row else None


def _unit_in_company(field, obj_id, company_id):
    """Is this BU / FU / location one of *company_id*'s own? (AC-185-16)"""
    if not obj_id:
        return True
    if not company_id:
        return False
    table = _UNIT_TABLES[field]
    return bool(query(
        f"SELECT 1 AS ok FROM {table} WHERE id=%s::uuid AND company_id=%s::uuid",
        (obj_id, company_id), one=True))


def _would_create_cycle(subject_id, manager_id):
    """True if *manager_id* already reports (directly or transitively) to the subject.

    Walks up the proposed manager's solid line; if the subject appears anywhere in
    it, approving the move would close a reporting loop (AC-185-13).
    """
    if not manager_id or not subject_id:
        return False
    return bool(query("""
        WITH RECURSIVE chain AS (
            SELECT employee_id, manager_id
            FROM manager_relationships
            WHERE employee_id=%s::uuid AND relationship_type='SOLID_LINE' AND is_current
            UNION ALL
            SELECT mr.employee_id, mr.manager_id
            FROM manager_relationships mr
            JOIN chain c ON mr.employee_id = c.manager_id
            WHERE mr.relationship_type='SOLID_LINE' AND mr.is_current
        )
        SELECT 1 AS ok FROM chain WHERE manager_id=%s::uuid LIMIT 1
    """, (manager_id, subject_id), one=True))


# ── Inbox page ────────────────────────────────────────────────────────────────

@app.route('/org-change')
@require_feature_access('org_change')
def org_change_inbox():
    return render_template('org_change/inbox.html')


# ── Request lifecycle ─────────────────────────────────────────────────────────

@app.route('/api/org-change/request', methods=['POST'])
@require_feature_access('org_change', 'w')
def api_org_change_request():
    """The single creation path for a position change / transfer.

    Both the org-tree drag-and-drop and the Transfer… entry point land here, so
    every guard below applies to both. Nothing is applied here — this only opens
    a PENDING request; the sequential chain in `org_change_service` decides.
    """
    u = _user()
    data = request.get_json() or {}
    subject_id = data.get('employee_id')
    if not subject_id:
        return jsonify({'error': 'employee_id is required'}), 400

    subj = query("SELECT company_id::text AS company_id, employment_status, "
                 "first_name||' '||last_name AS name "
                 "FROM employees WHERE id=%s::uuid", (subject_id,), one=True)
    if not subj:
        return jsonify({'error': 'Employee not found'}), 404
    subj = to_dict(subj)
    company_id = subj['company_id']
    if u['company_id'] and company_id != u['company_id'] and 'SYSTEM_ADMIN' not in u['roles']:
        return jsonify({'error': 'Employee is not in your company'}), 403
    # KAN-203 — nobody raises a position change about themselves, in any role.
    # Checked before the general initiator rule so the refusal can say WHY;
    # `_can_initiate_for` would refuse this anyway, with a message that would
    # read as nonsense to an HR admin ("your own reports" — it IS them).
    if _is_self(subject_id, u):
        _audit_self_action_refused('INITIATE', company_id, subject_id, u)
        return jsonify({'error': "You can't raise a position change for yourself. "
                                 "Ask your manager or HR to raise it for you."}), 403
    # CLAUDE.md org-change invariant 2 — the feature gate alone is NOT sufficient.
    if not _can_initiate_for(subject_id, u):
        return jsonify({'error': 'You can only request moves for your own reports (or as HR/Portal admin).'}), 403

    # AC-185-12 — a former employee cannot be transferred.
    if subj.get('employment_status') != 'ACTIVE':
        return jsonify({'error': f"{subj.get('name') or 'This employee'} is no longer active. "
                                 f"You can't transfer a former employee."}), 400

    proposed = {
        'business_unit_id':   data.get('business_unit_id') or None,
        'functional_unit_id': data.get('functional_unit_id') or None,
        'location_id':        data.get('location_id') or None,
        'manager_id':         data.get('manager_id') or None,
    }
    if not any(proposed.values()):
        return jsonify({'error': 'Nothing to change — pick a new unit, location or manager.'}), 400
    if proposed['manager_id'] == subject_id:
        return jsonify({'error': 'An employee cannot report to themselves.'}), 400

    # AC-185-16 / AC-185-19 — every proposed unit must belong to the SUBJECT's company.
    # A valid UUID from another tenant posted straight at the API is refused here.
    for field in _UNIT_TABLES:
        if not _unit_in_company(field, proposed[field], company_id):
            return jsonify({'error': 'That unit or location does not belong to this company.'}), 403

    # AC-185-13 — the proposed manager must be an active employee of the same company.
    if proposed['manager_id']:
        mgr = query("SELECT company_id::text AS company_id, employment_status "
                    "FROM employees WHERE id=%s::uuid", (proposed['manager_id'],), one=True)
        if not mgr:
            return jsonify({'error': 'The chosen manager was not found.'}), 400
        mgr = to_dict(mgr)
        if mgr['company_id'] != company_id:
            return jsonify({'error': 'That manager does not belong to this company.'}), 403
        if mgr.get('employment_status') != 'ACTIVE':
            return jsonify({'error': 'The chosen manager is no longer an active employee.'}), 400
        if _would_create_cycle(subject_id, proposed['manager_id']):
            return jsonify({'error': 'That manager reports to this employee — the move would '
                                     'create a reporting loop.'}), 400

    # AC-185-11 — a transfer that changes nothing is not a transfer.
    cur = svc.current_placement(subject_id)
    current_map = {'business_unit_id': cur.get('bu'), 'functional_unit_id': cur.get('fu'),
                   'location_id': cur.get('loc'), 'manager_id': cur.get('mgr')}
    if all(v == current_map[k] for k, v in proposed.items() if v):
        return jsonify({'error': 'That is where this employee already sits — nothing would change.'}), 400

    # AC-185-08 — one pending move per person. Two concurrent requests would both
    # apply, and the second would carry a stale "from" snapshot (CFL-5).
    existing = _pending_request_for(subject_id)
    if existing:
        return jsonify({
            'error': f"{subj.get('name') or 'This employee'} already has a position change waiting "
                     f"for approval. That one has to be decided or cancelled first.",
            'pending_request_id': existing,
        }), 409

    req_id = svc.create_request(company_id, subject_id, u['user_id'], proposed, data.get('reason'))
    return jsonify({'ok': True, 'id': req_id})


@app.route('/api/org-change/pending')
@require_feature_access('org_change')
def api_org_change_pending():
    return jsonify(svc.list_pending(_user()))


@app.route('/api/org-change/my-requests')
@login_required
def api_org_change_my():
    return jsonify(svc.list_my_requests(_user()))


@app.route('/api/org-change/pending-count')
@login_required
def api_org_change_pending_count():
    try:
        return jsonify({'count': len(svc.list_pending(_user()))})
    except Exception:
        return jsonify({'count': 0})


@app.route('/api/org-change/<req_id>/decide', methods=['POST'])
@require_feature_access('org_change', 'w')
def api_org_change_decide(req_id):
    data = request.get_json() or {}
    ok, result = svc.decide(req_id, _user(), data.get('action'), data.get('note'))
    if not ok:
        return jsonify({'error': result}), 400
    return jsonify({'ok': True, 'status': result})


@app.route('/api/org-change/<req_id>/cancel', methods=['POST'])
@login_required
def api_org_change_cancel(req_id):
    ok, result = svc.cancel(req_id, _user())
    if not ok:
        return jsonify({'error': result}), 400
    return jsonify({'ok': True, 'status': result})


@app.route('/api/org-change/prefill')
@require_feature_access('org_change', 'w')
def api_org_change_prefill():
    """Everything the request dialog needs, for BOTH entry points.

    Drag-and-drop passes `target` (the drop target, whose placement is proposed);
    the Transfer… entry point passes only `subject` and starts every select at
    "no change". The extra keys (`subject`, `subject_current_names`,
    `approval_chain`, `direct_reports`, `pending_request_id`) are additive — the
    drag-and-drop path keeps working unchanged.
    """
    u = _user()
    company_id = u['company_id']
    target_id  = request.args.get('target', '').strip() or None
    subject_id = request.args.get('subject', '').strip() or None

    subject = {}
    if subject_id:
        row = query("SELECT id::text, company_id::text AS company_id, employment_status, "
                    "first_name||' '||last_name AS name, employee_number, job_title "
                    "FROM employees WHERE id=%s::uuid", (subject_id,), one=True)
        if not row:
            return jsonify({'error': 'Employee not found'}), 404
        subject = to_dict(row)
        # Company scoping — never describe another tenant's employee (AC-185-18).
        if (u['company_id'] and subject.get('company_id') != u['company_id']
                and 'SYSTEM_ADMIN' not in u['roles']):
            return jsonify({'error': 'Employee is not in your company'}), 403

    target = svc.current_placement(target_id) if target_id else {}
    subject_current = svc.current_placement(subject_id) if subject_id else {}

    bus = [to_dict(r) for r in query(
        "SELECT id::text, name FROM business_units WHERE company_id=%s::uuid ORDER BY name", (company_id,))]
    fus = [to_dict(r) for r in query(
        "SELECT id::text, name, business_unit_id::text AS business_unit_id "
        "FROM functional_units WHERE company_id=%s::uuid ORDER BY name", (company_id,))]
    locs = [to_dict(r) for r in query(
        "SELECT id::text, name FROM locations WHERE company_id=%s::uuid ORDER BY name", (company_id,))]
    mgrs = [to_dict(r) for r in query(
        "SELECT id::text, first_name||' '||last_name AS name, job_title "
        "FROM employees WHERE company_id=%s::uuid AND employment_status='ACTIVE' "
        "ORDER BY last_name", (company_id,))]

    # "Currently:" row — names, not ids (UX spec §6.2). PD1: no manager reads as such.
    by_id = lambda rows, oid: next((r['name'] for r in rows if r['id'] == oid), None)
    current_names = {}
    reports = 0
    pending_id = None
    if subject_id:
        current_names = {
            'manager':         by_id(mgrs, subject_current.get('mgr')),
            'business_unit':   by_id(bus,  subject_current.get('bu')),
            'functional_unit': by_id(fus,  subject_current.get('fu')),
            'location':        by_id(locs, subject_current.get('loc')),
        }
        # AC-185-10 — a manager's team does NOT move with them; say so before submit.
        cnt = query("""
            SELECT COUNT(*)::int AS c
            FROM manager_relationships mr
            JOIN employees e ON e.id = mr.employee_id AND e.employment_status='ACTIVE'
            WHERE mr.manager_id=%s::uuid AND mr.relationship_type='SOLID_LINE' AND mr.is_current
        """, (subject_id,), one=True)
        reports = (cnt or {}).get('c') or 0
        pending_id = _pending_request_for(subject_id)

    return jsonify({
        'target': target, 'subject_current': subject_current,
        'business_units': bus, 'functional_units': fus,
        'locations': locs, 'managers': mgrs,
        'subject': subject,
        'subject_current_names': current_names,
        'approval_chain': _approval_chain(company_id or subject.get('company_id')),
        'direct_reports': reports,
        'pending_request_id': pending_id,
    })


# ── Admin: workflow configuration ─────────────────────────────────────────────

@app.route('/admin/org-change-workflow')
@require_feature_access('org_structure', 'w')
def admin_org_change_workflow():
    return render_template('admin/org_change_workflow.html')


@app.route('/api/admin/org-change-workflow')
@require_feature_access('org_structure', 'w')
def api_admin_org_change_workflow_get():
    u = _user()
    company_id = u['company_id']
    steps = svc.workflow_steps(company_id) if company_id else []
    # Resolve display names for EMPLOYEE steps
    for s in steps:
        if s.get('approver_type') == 'EMPLOYEE' and s.get('approver_employee_id'):
            s['approver_name'] = svc._emp_name(s['approver_employee_id'])
    role_names = [r['name'] for r in query(
        "SELECT DISTINCT name FROM roles WHERE name <> 'SYSTEM_ADMIN' ORDER BY name")]
    employees = [to_dict(r) for r in query(
        "SELECT id::text, first_name||' '||last_name AS name, job_title "
        "FROM employees WHERE company_id=%s::uuid AND employment_status='ACTIVE' ORDER BY last_name",
        (company_id,))] if company_id else []
    configured = bool(query(
        "SELECT 1 FROM org_change_workflows WHERE company_id=%s::uuid", (company_id,), one=True)) if company_id else False
    return jsonify({'steps': steps, 'roles': role_names, 'employees': employees, 'configured': configured})


@app.route('/api/admin/org-change-workflow', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_admin_org_change_workflow_save():
    u = _user()
    company_id = u['company_id']
    if not company_id:
        return jsonify({'error': 'Select a company first.'}), 400
    data  = request.get_json() or {}
    steps = data.get('steps') or []
    if not steps:
        return jsonify({'error': 'Add at least one approval level.'}), 400
    svc.save_workflow(company_id, data.get('name'), steps)
    return jsonify({'ok': True})
