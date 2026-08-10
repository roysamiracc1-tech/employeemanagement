"""Performance review cycles and eligibility — EP44 P0 (KAN-219, KAN-220).

    `performance:r`  read — seeded to EVERY role, because an employee must be able
                     to read their own review. Row scoping decides WHOSE.
    `performance:w`  **administer the company's review rounds** — open, configure,
                     close. HR_ADMIN + PORTAL_ADMIN, deliberately NOT a manager:
                     a line manager must not open or close the company's round.

⚠ **An open design question, left open rather than answered early.** A manager
writing an assessment and an employee writing a self-assessment are also WRITES,
and they must not need this admin grant. That is the same shape as CFL-42-35 —
where `job_architecture:w` turned out to mean "author for your own reports" while
ladder configuration needed `org_structure:w`. It is raised in BACKLOG.md against
the assessment stories rather than settled here, because inventing a sixth feature
code before the story that needs it is how a permission model acquires codes
nobody can explain.

`require_roles` is deliberately never imported: hardcoded role lists on feature
routes are forbidden (CLAUDE.md).
"""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import require_feature_access, can_access_feature
from app.services.company_scope import current_company_id
from app.services import performance_service as svc
from app.services.performance_service import CycleError


def _user():
    return {'user_id': session.get('user_id'),
            'employee_id': session.get('employee_id'),
            'company_id': current_company_id(),
            'roles': session.get('roles', [])}


def _company_or_400():
    cid = current_company_id()
    if not cid:
        return None, (jsonify({'error': 'Select a company first.'}), 400)
    return cid, None


def _fail(exc):
    return jsonify({'error': str(exc)}), 400


# ── The admin page ────────────────────────────────────────────────────────────

@app.route('/admin/performance-cycles')
@require_feature_access('performance', 'w')
def admin_performance_cycles():
    cid = current_company_id()
    return render_template(
        'admin/performance_cycles.html',
        has_company=bool(cid),
        cycles=svc.list_cycles(cid) if cid else [],
        active=svc.active_cycle(cid) if cid else None,
        states=[{'value': s, 'label': svc.STATE_LABELS[s]} for s in svc.CYCLE_STATES],
        default_cutoff=svc.DEFAULT_JOINER_CUTOFF_DAYS,
        default_excluded=svc.DEFAULT_EXCLUDED_TYPES,
    )


# ── Cycle APIs — `performance:w` ─────────────────────────────────────────────

@app.route('/api/performance/cycles')
@require_feature_access('performance', 'w')
def api_cycles():
    cid, err = _company_or_400()
    if err:
        return err
    return jsonify({'cycles': svc.list_cycles(cid), 'active': svc.active_cycle(cid)})


@app.route('/api/performance/cycles', methods=['POST'])
@require_feature_access('performance', 'w')
def api_create_cycle():
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        cyc = svc.create_cycle(
            cid, d.get('name'), d.get('period_year'),
            d.get('opens_on'), d.get('closes_on'),
            self_assessment_deadline=d.get('self_assessment_deadline'),
            joiner_cutoff_days=d.get('joiner_cutoff_days'),
            excluded_employment_types=d.get('excluded_employment_types'),
            actor=_user())
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True, 'id': cyc})


@app.route('/api/performance/cycles/<cycle_id>', methods=['PATCH'])
@require_feature_access('performance', 'w')
def api_update_cycle(cycle_id):
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    allowed = {k: d[k] for k in
               ('name', 'opens_on', 'closes_on', 'self_assessment_deadline',
                'joiner_cutoff_days', 'excluded_employment_types') if k in d}
    try:
        svc.update_cycle(cid, cycle_id, actor=_user(), **allowed)
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True})


@app.route('/api/performance/cycles/<cycle_id>/advance', methods=['POST'])
@require_feature_access('performance', 'w')
def api_advance_cycle(cycle_id):
    """Move the round forward. Forward only — a round is what assessments point at."""
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        out = svc.advance_cycle(cid, cycle_id, d.get('to_status'), actor=_user())
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


@app.route('/api/performance/cycles/<cycle_id>/close', methods=['POST'])
@require_feature_access('performance', 'w')
def api_close_cycle(cycle_id):
    cid, err = _company_or_400()
    if err:
        return err
    try:
        out = svc.close_cycle(cid, cycle_id, actor=_user())
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


@app.route('/api/performance/cycles/<cycle_id>', methods=['DELETE'])
@require_feature_access('performance', 'w')
def api_discard_cycle(cycle_id):
    cid, err = _company_or_400()
    if err:
        return err
    try:
        svc.discard_draft(cid, cycle_id, actor=_user())
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True})


# ── Eligibility ──────────────────────────────────────────────────────────────

@app.route('/api/performance/cycles/<cycle_id>/eligibility/preview')
@require_feature_access('performance', 'w')
def api_preview_eligibility(cycle_id):
    """Who WOULD be in the round. Changes nothing.

    Shown before opening, because opening takes the snapshot that every manager's
    list is built from — this touches everybody at once.
    """
    cid, err = _company_or_400()
    if err:
        return err
    try:
        return jsonify(svc.preview_eligibility(cid, cycle_id))
    except CycleError as exc:
        return _fail(exc)


@app.route('/api/performance/cycles/<cycle_id>/eligibility/snapshot', methods=['POST'])
@require_feature_access('performance', 'w')
def api_take_snapshot(cycle_id):
    """Freeze the list, or re-evaluate it and report what changed."""
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        out = svc.take_snapshot(cid, cycle_id, actor=_user(),
                               re_evaluate=bool(d.get('re_evaluate')))
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


@app.route('/api/performance/cycles/<cycle_id>/participants')
@require_feature_access('performance')
def api_participants(cycle_id):
    """The frozen list.

    **Row-scoped** (AC-220-11): an admin sees the company's, a manager sees their
    own reports', and anybody else sees only themselves. Asserted at the payload,
    because a URL is a guess anybody can make.
    """
    cid, err = _company_or_400()
    if err:
        return err
    roles = session.get('roles', [])
    me = session.get('employee_id')
    is_admin = can_access_feature('performance', 'w')
    try:
        if is_admin:
            rows = svc.participants(cid, cycle_id)
        else:
            rows = svc.participants(cid, cycle_id, manager_employee_id=me)
            if not rows:
                rows = [r for r in svc.participants(cid, cycle_id)
                        if r['employee_id'] == me]
        out = {'participants': rows}
        if is_admin:
            out['coverage'] = svc.coverage(cid, cycle_id)
    except CycleError as exc:
        return _fail(exc)
    return jsonify(out)


@app.route('/api/performance/cycles/<cycle_id>/participants/<employee_id>',
           methods=['PUT'])
@require_feature_access('performance', 'w')
def api_override_participation(cycle_id, employee_id):
    """Include or exclude one person. The reason is mandatory."""
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    if 'include' not in d:
        return jsonify({'error': 'Say whether they are in or out.'}), 400
    try:
        svc.override_participation(cid, cycle_id, employee_id,
                                  bool(d.get('include')),
                                  reason=d.get('reason'), actor=_user())
    except CycleError as exc:
        return _fail(exc)
    return jsonify({'ok': True})
