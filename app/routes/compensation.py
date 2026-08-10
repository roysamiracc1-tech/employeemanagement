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
from flask import session, request, jsonify, render_template, Response

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


# ══════════════════════════════════════════════════════════════════════════════
# KAN-191 — everyone on a level
#
# Two surfaces, two audiences, two gates:
#
#   THE MAPPING SCREEN     HR, `org_structure:w` — bulk, title-driven, one sitting
#   STEP ASSESSMENT        a MANAGER, for their own reports only
#
# The manager surface is gated `job_architecture:w`, and this is the one place
# that grant is correct: it is roadmap/step authoring for your own people, which
# is exactly what CFL-42-35 says it means. It is still NOT ladder editing.
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/job-mapping')
@require_feature_access('org_structure', 'w')
def admin_job_mapping():
    """The R-2 screen. 41 distinct titles at Acme and 75 at Telia for 146 people —
    whether this screen is usable decides whether the rollout finishes."""
    cid = current_company_id()
    return render_template(
        'admin/job_mapping.html',
        titles=svc.title_counts(cid) if cid else [],
        levels=svc.list_levels(cid) if cid else [],
        coverage=svc.coverage(cid) if cid else None,
        has_company=bool(cid),
    )


@app.route('/api/job-mapping/titles')
@require_feature_access('org_structure', 'w')
def api_title_counts():
    cid, err = _company_or_400()
    if err:
        return err
    return jsonify({'titles': svc.title_counts(cid), 'coverage': svc.coverage(cid)})


@app.route('/api/job-mapping/save', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_save_title_map():
    """Record the decisions WITHOUT placing anybody — mapping 75 titles is not
    one sitting, so it has to be saveable and resumable."""
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        n = svc.save_title_map(cid, d.get('mappings') or [], actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, 'saved': n})


@app.route('/api/job-mapping/apply', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_apply_title_map():
    """Place everyone whose title is mapped. **Dry run unless `confirm` is true.**

    This touches the whole workforce at once and there is no undo, so the screen
    shows what WOULD happen first. Anyone already on a level is skipped, never
    overwritten — a re-run must not quietly undo a deliberate correction.
    """
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    try:
        result = svc.apply_title_map(cid, actor=_user(),
                                     dry_run=not bool(d.get('confirm')))
    except LadderError as exc:
        return _fail(exc)
    return jsonify(result)


@app.route('/api/job-mapping/export.csv')
@require_feature_access('org_structure', 'w')
def api_export_title_map():
    """CSV out, so the mapping can be done in a spreadsheet by the people who
    know the titles and brought back in. Import is the exact same columns."""
    import csv
    import io
    cid = current_company_id()
    if not cid:
        return jsonify({'error': 'Select a company first.'}), 400
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['job_title', 'headcount', 'family', 'level_ordinal', 'level_title'])
    for t in svc.title_counts(cid):
        w.writerow([t['job_title'], t['headcount'],
                    t.get('mapped_family_name') or '',
                    t.get('mapped_level_ordinal') or '',
                    t.get('mapped_level_title') or ''])
    return Response(buf.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition':
                             'attachment; filename=job-title-mapping.csv'})


@app.route('/api/job-mapping/import', methods=['POST'])
@require_feature_access('org_structure', 'w')
def api_import_title_map():
    """CSV in. **Row-level errors are reported with their line number, never
    silently skipped** — a bulk import that quietly drops rows is how a mapping
    project appears finished while people are still unplaced."""
    import csv
    import io
    cid, err = _company_or_400()
    if err:
        return err
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'Choose a CSV file to import.'}), 400
    try:
        text = f.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        return jsonify({'error': 'That file is not UTF-8 text. Export a fresh '
                                 'copy and edit that.'}), 400

    # Resolve level identity from (ordinal, title) — the human-readable columns
    # the export produced, so a spreadsheet round-trip needs no UUIDs.
    by_key = {}
    for l in svc.list_levels(cid):
        by_key[(str(l['ordinal']), (l['title'] or '').strip().lower())] = l['id']
        by_key[(str(l['ordinal']), '')] = l['id']

    mappings, errors = [], []
    for i, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        title = (row.get('job_title') or '').strip()
        if not title:
            errors.append({'line': i, 'error': 'job_title is empty'})
            continue
        ordinal = (row.get('level_ordinal') or '').strip()
        level_title = (row.get('level_title') or '').strip().lower()
        if not ordinal:
            mappings.append({'job_title': title, 'job_level_id': None})
            continue
        lid = by_key.get((ordinal, level_title)) or by_key.get((ordinal, ''))
        if not lid:
            errors.append({'line': i,
                           'error': f'no level {ordinal} "{row.get("level_title") or ""}" '
                                    f'in this company'})
            continue
        mappings.append({'job_title': title, 'job_level_id': lid})

    saved = 0
    if mappings:
        try:
            saved = svc.save_title_map(cid, mappings, actor=_user())
        except LadderError as exc:
            return _fail(exc)
    return jsonify({'ok': not errors, 'saved': saved, 'errors': errors})


# ── Step assessment — the manager's surface ───────────────────────────────────

@app.route('/my-team/steps')
@require_feature_access('job_architecture', 'w')
def my_team_steps():
    """A manager assesses their own reports against the described expectations.

    Distributed on purpose: one HR person assessing 146 people is a project
    nobody finishes; forty managers assessing three or four each is a ten-minute
    task — and they are the only people who can do it correctly.
    """
    cid = current_company_id()
    emp = session.get('employee_id')
    return render_template(
        'employees/step_assessment.html',
        reports=svc.pending_assessments(cid, emp) if (cid and emp) else [],
        has_company=bool(cid),
    )


@app.route('/api/step-assessment/reports')
@require_feature_access('job_architecture', 'w')
def api_step_reports():
    cid, err = _company_or_400()
    if err:
        return err
    return jsonify({'reports': svc.pending_assessments(cid, session.get('employee_id'))})


@app.route('/api/step-assessment/<employee_id>', methods=['PUT'])
@require_feature_access('job_architecture', 'w')
def api_assess_step(employee_id):
    """Record the assessment.

    An HR/Portal admin may override a manager's judgement, and then the reason is
    mandatory — they are not the person who can judge the work, so an override
    has to say why it was made anyway.
    """
    cid, err = _company_or_400()
    if err:
        return err
    d = request.get_json() or {}
    roles = session.get('roles', [])
    is_own_report = any(r['employee_id'] == employee_id
                        for r in svc.pending_assessments(cid, session.get('employee_id')))
    is_admin = bool({'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'} & set(roles))
    if not is_own_report and not is_admin:
        # Not a feature-gate question: the gate says "may assess", this says
        # "may assess THIS PERSON". Same shape as the org-change initiator rule.
        return jsonify({'error': 'You can only assess your own direct reports.'}), 403
    try:
        out = svc.assess_step(cid, employee_id, d.get('step_no'), actor=_user(),
                              reason=d.get('reason'),
                              is_hr_override=(is_admin and not is_own_report))
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


# ══════════════════════════════════════════════════════════════════════════════
# KAN-207 — step roadmaps
#
# Two surfaces:
#   /my-ladder        the EMPLOYEE's own view. `job_architecture:r` — seeded to
#                     every role, because visibility is the entire point.
#   the manager's authoring dialog, on /my-team/steps — `job_architecture:w`,
#                     row-scoped to their own reports. This IS what the fourth
#                     feature code was created for (CFL-42-35).
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/my-ladder')
@require_feature_access('job_architecture')
def my_ladder():
    """What the ladder means for ME. **Visible to the employee, not optional** —
    transparency is the stated purpose, so if the employee cannot see it we have
    not built it.

    Renders whether or not the company displays step numbers: with the switch off
    the roadmap still reads in full, without a step number and without a
    "you are here" marker (A2 option (b)). Hiding the roadmap too would discard
    the transparency the owner asked for twice in order to hide a label.
    """
    cid = current_company_id()
    emp = session.get('employee_id')
    if not cid or not emp:
        return render_template('employees/my_ladder.html', has_context=False)

    roadmap = svc.live_roadmap(cid, emp)
    if roadmap:
        # It is an FYI, not a call to action — retire it from the bell now that
        # they have actually read it.
        svc.mark_roadmap_seen(roadmap['id'])
    return render_template(
        'employees/my_ladder.html',
        has_context=True,
        where=svc.next_step_target(cid, emp),
        roadmap=roadmap,
        history=[r for r in svc.roadmap_history(cid, emp) if not r['is_live']],
        shows_step=svc.displays_step(cid),
        ladder=svc.ladder(cid),
    )


@app.route('/api/roadmap/<employee_id>')
@require_feature_access('job_architecture')
def api_roadmap(employee_id):
    """A roadmap is about ONE named person and is nobody else's business.

    An employee reads their own; a manager reads their own reports'; HR/Portal
    admin may read within their company. Asserted **at the payload**, not only in
    the nav — a URL is a guess anybody can make.
    """
    cid, err = _company_or_400()
    if err:
        return err
    me = session.get('employee_id')
    roles = session.get('roles', [])
    is_admin = bool({'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'} & set(roles))
    is_own = (str(employee_id) == str(me))
    manages = any(r['employee_id'] == employee_id
                  for r in svc.pending_assessments(cid, me)) if me else False
    if not (is_own or manages or is_admin):
        return jsonify({'error': 'A roadmap is only visible to the person it is '
                                 'about, their manager, and HR.'}), 403
    return jsonify({
        'where': svc.next_step_target(cid, employee_id),
        'live': svc.live_roadmap(cid, employee_id),
        'history': svc.roadmap_history(cid, employee_id),
        'contexts': [{'value': v, 'label': svc.REVIEW_CONTEXT_LABELS[v]}
                     for v in svc.REVIEW_CONTEXTS],
        'shows_step': svc.displays_step(cid),
    })


@app.route('/api/roadmap/<employee_id>', methods=['POST'])
@require_feature_access('job_architecture', 'w')
def api_author_roadmap(employee_id):
    """Write a roadmap. Row-scoped to the author's own reports, or HR/Portal.

    The feature gate says "may author roadmaps"; this says "may author for THIS
    person". Same shape as the org-change initiator rule — the flag alone is
    never sufficient.
    """
    cid, err = _company_or_400()
    if err:
        return err
    me = session.get('employee_id')
    roles = session.get('roles', [])
    is_admin = bool({'HR_ADMIN', 'PORTAL_ADMIN', 'SYSTEM_ADMIN'} & set(roles))
    manages = any(r['employee_id'] == employee_id
                  for r in svc.pending_assessments(cid, me)) if me else False
    if not (manages or is_admin):
        return jsonify({'error': 'You can only write a roadmap for your own '
                                 'direct reports.'}), 403
    d = request.get_json() or {}
    try:
        out = svc.author_roadmap(
            cid, employee_id, d.get('content'), d.get('review_context'),
            review_date=(d.get('review_date') or None),
            actor=_user(),
            author_label=session.get('user_name') or 'Their manager')
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


@app.route('/api/roadmap/<employee_id>/confirm-discussed', methods=['POST'])
@require_feature_access('job_architecture')
def api_confirm_roadmap_discussed(employee_id):
    """**The employee confirms the conversation happened. Not agreement.**

    CFL-42-50 — recording "agreed" when somebody merely read it is a false record
    about a person. Only the SUBJECT may do this: a manager confirming on their
    report's behalf would be exactly the false record the wording avoids.
    """
    cid, err = _company_or_400()
    if err:
        return err
    if str(employee_id) != str(session.get('employee_id')):
        return jsonify({'error': 'Only the person a roadmap is about can confirm '
                                 'they discussed it.'}), 403
    try:
        out = svc.acknowledge_roadmap(cid, employee_id, actor=_user())
    except LadderError as exc:
        return _fail(exc)
    return jsonify({'ok': True, **out})


@app.route('/api/roadmap/mine/unconfirmed')
@require_feature_access('job_architecture', 'w')
def api_unconfirmed_roadmaps():
    """The author's own follow-up list — what replaces a blocking workflow.

    An unacknowledged roadmap is still live and blocks nothing: a non-responsive
    employee must not be able to freeze their own development plan. So the
    follow-up goes to the person who can have the conversation.
    """
    cid, err = _company_or_400()
    if err:
        return err
    return jsonify({'unconfirmed': svc.unacknowledged_roadmaps(
        cid, session.get('user_id'))})
