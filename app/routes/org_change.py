"""Position-change (org-change) request + approval routes."""
from flask import session, request, render_template, jsonify, redirect, url_for, flash

from app import app
from app.db import query, to_dict
from app.auth import login_required, require_feature_access, require_roles
from app.helpers import employee_solid_manager
from app.services import org_change_service as svc

_ADMIN_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')


def _user():
    """Light user context for the workflow engine."""
    return {
        'user_id':     session.get('user_id'),
        'employee_id': session.get('employee_id'),
        'company_id':  session.get('company_id') or session.get('admin_company_id') or None,
        'roles':       session.get('roles', []),
    }


def _can_initiate_for(subject_id, u):
    """Requester must manage the subject (solid line) OR be HR/Portal/System admin."""
    if {'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'} & set(u.get('roles') or []):
        return True
    return employee_solid_manager(subject_id) == u.get('employee_id')


# ── Inbox page ────────────────────────────────────────────────────────────────

@app.route('/org-change')
@require_feature_access('org_change')
def org_change_inbox():
    return render_template('org_change/inbox.html')


# ── Request lifecycle ─────────────────────────────────────────────────────────

@app.route('/api/org-change/request', methods=['POST'])
@require_feature_access('org_change', 'w')
def api_org_change_request():
    u = _user()
    data = request.get_json() or {}
    subject_id = data.get('employee_id')
    if not subject_id:
        return jsonify({'error': 'employee_id is required'}), 400

    subj = query("SELECT company_id::text AS company_id FROM employees WHERE id=%s::uuid",
                 (subject_id,), one=True)
    if not subj:
        return jsonify({'error': 'Employee not found'}), 404
    company_id = subj['company_id']
    if u['company_id'] and company_id != u['company_id'] and 'SYSTEM_ADMIN' not in u['roles']:
        return jsonify({'error': 'Employee is not in your company'}), 403
    if not _can_initiate_for(subject_id, u):
        return jsonify({'error': 'You can only request moves for your own reports (or as HR/Portal admin).'}), 403

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
    """Target's current placement + company org-unit option lists for the drop modal."""
    u = _user()
    company_id = u['company_id']
    target_id  = request.args.get('target', '').strip() or None
    subject_id = request.args.get('subject', '').strip() or None

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

    return jsonify({
        'target': target, 'subject_current': subject_current,
        'business_units': bus, 'functional_units': fus,
        'locations': locs, 'managers': mgrs,
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
