"""Job architecture / compensation routes — the ladder configurator (KAN-190).

⚠ **TWO GATES ON ONE SCREEN, AND THEY ARE DIFFERENT ON PURPOSE (CFL-42-35).**

    READING the ladder      -> `job_architecture:r`   (seeded to EVERY role)
    CONFIGURING the ladder  -> `org_structure:w`      (HR_ADMIN + PORTAL_ADMIN, NO manager)

`job_architecture:w` is **not** a ladder-editing grant. It governs **roadmap
authoring** for a manager's own reports (KAN-207). Both halves of CFL-42-35
matter: a manager must be able to author roadmaps, and a manager must **not** be
able to edit the company's job architecture. A tenant that genuinely wants
engineering managers to own the ladder creates a role and grants
`org_structure:w` — the permission matrix already solves that and it needs no
code here.

The level's base pay point and step increment are a different gate again
(`compensation:w`, KAN-206) — one screen, three gates, as ruled for Compensation
Settings. Those fields are not in this module.

`require_roles` is deliberately never imported: hardcoded role lists on feature
routes are forbidden (CLAUDE.md), and a grep-assert test enforces it.
"""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import require_feature_access, can_access_feature
from app.services.company_scope import current_company_id
from app.services import job_architecture_service as svc
from app.services.job_architecture_service import LadderError


def _user():
    return {'user_id': session.get('user_id'),
            'employee_id': session.get('employee_id'),
            'company_id': current_company_id(),
            'roles': session.get('roles', [])}


def _company_or_400():
    """Every ladder read and write is company-scoped; no company, no ladder."""
    cid = current_company_id()
    if not cid:
        return None, (jsonify({'error': 'Select a company first.'}), 400)
    return cid, None


def _fail(exc):
    """A business-rule refusal is a 400 carrying its own explanation."""
    return jsonify({'error': str(exc)}), 400


# ── The configurator page ─────────────────────────────────────────────────────

@app.route('/admin/job-architecture')
@require_feature_access('job_architecture')
def admin_job_architecture():
    """Read-gated only. The page renders for anyone who may READ the ladder;
    the editing affordances are hidden unless they may configure it, and every
    write endpoint re-checks server-side."""
    cid = current_company_id()
    return render_template(
        'admin/job_architecture.html',
        can_configure=can_access_feature('org_structure', 'w'),
        ladder=svc.ladder(cid) if cid else [],
        completeness=svc.ladder_completeness(cid) if cid else None,
        max_step_count=svc.MAX_STEP_COUNT,
        min_step_count=svc.MIN_STEP_COUNT,
        max_ordinal=svc.MAX_ORDINAL,
        has_company=bool(cid),
    )


# ── Read APIs — `job_architecture:r` ─────────────────────────────────────────

@app.route('/api/job-architecture/ladder')
@require_feature_access('job_architecture')
def api_ladder():
    cid, err = _company_or_400()
    if err:
        return err
    return jsonify({'families': svc.ladder(cid),
                    'completeness': svc.ladder_completeness(cid)})


@app.route('/api/job-architecture/levels/<level_id>/steps')
@require_feature_access('job_architecture')
def api_level_steps(level_id):
    """Every step of a level, authored or not.

    Readable by every role on purpose: an employee must be able to read their own
    step and the next one, which is the transparency the owner asked for twice.
    """
    cid, err = _company_or_400()
    if err:
        return err
    try:
        return jsonify(svc.level_steps(cid, level_id))
    except LadderError as exc:
        return _fail(exc)


# ── Write APIs — `org_structure:w` (NOT job_architecture:w) ───────────────────

@app.route('/api/job-architecture/families', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_create_family():
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        fid = svc.create_family(cid, d.get('code'), d.get('name'),
                                description=d.get('description'),
                                sort_order=d.get('sort_order') or 0,
                                actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, 'id': fid})


@app.route('/api/job-architecture/families/<family_id>', methods=['PATCH'])
@require_feature_access('org_structure', 'w')
def api_update_family(family_id):
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        svc.update_family(cid, family_id, name=d.get('name'),
                          description=d.get('description'),
                          sort_order=d.get('sort_order'),
                          is_active=d.get('is_active'), actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True})


@app.route('/api/job-architecture/levels', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_create_level():
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    # `step_count` is required — absent is NOT zero and NOT five. The
    # configurator must have asked; a missing value means it did not.
    if d.get('step_count') in (None, ''):
        return jsonify({'error': 'Say how many steps this level has above entry — '
                                 'there is deliberately no default, because levels '
                                 'are genuinely different distances apart.'}), 400
    try:
        lid = svc.create_level(cid, d.get('job_family_id'), d.get('ordinal'),
                               d.get('title'), d.get('step_count'),
                               short_code=d.get('short_code'),
                               description=d.get('description'), actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, 'id': lid})


@app.route('/api/job-architecture/levels/<level_id>', methods=['PATCH'])
@require_feature_access('org_structure', 'w')
def api_update_level(level_id):
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        svc.update_level(cid, level_id, title=d.get('title'),
                         short_code=d.get('short_code'),
                         description=d.get('description'),
                         ordinal=d.get('ordinal'),
                         step_count=d.get('step_count'),
                         is_active=d.get('is_active'), actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True})


@app.route('/api/job-architecture/levels/<level_id>/steps/<int:step_no>', methods=['PUT'])
@require_feature_access('org_structure', 'w')
def api_save_step(level_id, step_no):
    """Author one step's expectations. **Save is publish** — no draft state."""
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        svc.save_step_expectation(cid, level_id, step_no,
                                  d.get('summary'), d.get('description'),
                                  drafted_by=d.get('drafted_by'), actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True})
