import datetime

from flask import session, redirect, url_for, request, render_template, flash, jsonify

from app import app
from app.db import query, execute, insert_returning, to_dict
from app.auth import login_required, require_roles
from app.helpers import (vacation_types_for_employee, employee_solid_manager,
                          used_days, rule_label)

MGMT_VACATION_ROLES = ['SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']


# ── Admin: vacation type management ──────────────────────────────────────────

_ADMIN_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')


def _vac_company_scope():
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        return None
    return session.get('company_id') or None


@app.route('/admin/vacation-types')
@require_roles(*_ADMIN_ROLES)
def admin_vacation_types():
    co_id = _vac_company_scope()
    co_filter = "WHERE vt.company_id = %s::uuid" if co_id else ""
    rows = query(f"""
        SELECT vt.id::text, vt.name, vt.description, vt.max_days_per_year,
               vt.is_paid, vt.color, vt.is_active,
               c.name AS company_name,
               ARRAY_AGG(l.name ORDER BY l.name) FILTER (WHERE l.name IS NOT NULL) AS locations
        FROM vacation_types vt
        JOIN companies c ON c.id = vt.company_id
        LEFT JOIN vacation_type_locations vtl ON vtl.vacation_type_id = vt.id
        LEFT JOIN locations l ON l.id = vtl.location_id
        {co_filter}
        GROUP BY vt.id, c.name
        ORDER BY c.name, vt.name
    """, (co_id,) if co_id else ())
    return render_template('admin/vacation_types.html',
                           types=[to_dict(r) for r in rows])


@app.route('/admin/vacation-types/new', methods=['GET', 'POST'])
@require_roles(*_ADMIN_ROLES)
def admin_vacation_type_new():
    co_id     = _vac_company_scope()
    companies = [] if co_id else [to_dict(r) for r in query("SELECT id::text, name FROM companies WHERE is_active ORDER BY name")]
    locations = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]

    if request.method == 'POST':
        company_id = co_id or request.form.get('company_id')
        name       = request.form.get('name', '').strip()
        desc       = request.form.get('description', '').strip() or None
        max_days   = request.form.get('max_days_per_year', '').strip() or None
        is_paid    = request.form.get('is_paid') == '1'
        color      = request.form.get('color', '#3b82f6').strip()
        loc_ids    = request.form.getlist('location_ids')

        if not company_id or not name:
            flash('Company and name are required.', 'error')
            return redirect(url_for('admin_vacation_type_new'))

        vt = insert_returning("""
            INSERT INTO vacation_types (company_id, name, description, max_days_per_year, is_paid, color)
            VALUES (%s::uuid,%s,%s,%s,%s,%s) RETURNING id::text
        """, (company_id, name, desc, int(max_days) if max_days else None, is_paid, color))

        for lid in loc_ids:
            execute("INSERT INTO vacation_type_locations VALUES (%s::uuid,%s::uuid)", (vt['id'], lid))

        for rt, rv in zip(request.form.getlist('rule_type'), request.form.getlist('rule_value')):
            if rt and rv:
                execute("INSERT INTO vacation_type_rules (vacation_type_id,rule_type,rule_value) VALUES (%s::uuid,%s,%s)",
                        (vt['id'], rt, rv))

        flash(f'Vacation type "{name}" created.', 'success')
        return redirect(url_for('admin_vacation_types'))

    return render_template('admin/vacation_type_form.html',
                           vt=None, action='new',
                           companies=companies, locations=locations,
                           locked_company_id=co_id)


@app.route('/admin/vacation-types/<vt_id>/edit', methods=['GET', 'POST'])
@require_roles(*_ADMIN_ROLES)
def admin_vacation_type_edit(vt_id):
    co_id     = _vac_company_scope()
    companies = [] if co_id else [to_dict(r) for r in query("SELECT id::text, name FROM companies WHERE is_active ORDER BY name")]
    locations = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]
    vt_row = query(
        "SELECT id::text,company_id::text,name,description,max_days_per_year,"
        "is_paid,color,is_active FROM vacation_types WHERE id=%s::uuid",
        (vt_id,), one=True,
    )
    if not vt_row:
        flash('Not found.', 'error')
        return redirect(url_for('admin_vacation_types'))
    if co_id and to_dict(vt_row).get('company_id') != co_id:
        flash('That vacation type does not belong to your company.', 'error')
        return redirect(url_for('admin_vacation_types'))

    assigned_locs  = [r['location_id'] for r in query(
        "SELECT location_id::text FROM vacation_type_locations WHERE vacation_type_id=%s::uuid", (vt_id,))]
    existing_rules = [to_dict(r) for r in query(
        "SELECT rule_type, rule_value FROM vacation_type_rules WHERE vacation_type_id=%s::uuid ORDER BY created_at",
        (vt_id,))]

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        desc      = request.form.get('description', '').strip() or None
        max_days  = request.form.get('max_days_per_year', '').strip() or None
        is_paid   = request.form.get('is_paid') == '1'
        color     = request.form.get('color', '#3b82f6').strip()
        is_active = request.form.get('is_active') == '1'
        loc_ids   = request.form.getlist('location_ids')

        execute("""
            UPDATE vacation_types SET name=%s, description=%s, max_days_per_year=%s,
                is_paid=%s, color=%s, is_active=%s WHERE id=%s::uuid
        """, (name, desc, int(max_days) if max_days else None, is_paid, color, is_active, vt_id))

        execute("DELETE FROM vacation_type_locations WHERE vacation_type_id=%s::uuid", (vt_id,))
        for lid in loc_ids:
            execute("INSERT INTO vacation_type_locations VALUES (%s::uuid,%s::uuid)", (vt_id, lid))

        execute("DELETE FROM vacation_type_rules WHERE vacation_type_id=%s::uuid", (vt_id,))
        for rt, rv in zip(request.form.getlist('rule_type'), request.form.getlist('rule_value')):
            if rt and rv:
                execute("INSERT INTO vacation_type_rules (vacation_type_id,rule_type,rule_value) VALUES (%s::uuid,%s,%s)",
                        (vt_id, rt, rv))

        flash(f'"{name}" updated.', 'success')
        return redirect(url_for('admin_vacation_types'))

    return render_template('admin/vacation_type_form.html',
                           vt=to_dict(vt_row), action='edit',
                           companies=companies, locations=locations,
                           assigned_locs=assigned_locs,
                           existing_rules=existing_rules)


@app.route('/api/admin/vacation-rules')
@require_roles('SYSTEM_ADMIN')
def api_admin_vacation_rules():
    ids = [i.strip() for i in request.args.get('ids', '').split(',') if i.strip()]
    if not ids:
        return jsonify({})
    rows = query(
        "SELECT vacation_type_id::text, rule_type, rule_value "
        "FROM vacation_type_rules WHERE vacation_type_id = ANY(%s::uuid[]) ORDER BY created_at",
        (ids,),
    )
    result = {i: [] for i in ids}
    for r in rows:
        result[r['vacation_type_id']].append({'rule_type': r['rule_type'], 'rule_value': r['rule_value']})
    return jsonify(result)


# ── Employee vacation ─────────────────────────────────────────────────────────

@app.route('/vacation')
@login_required
def vacation_page():
    emp_id = session['employee_id']
    mgr_id = employee_solid_manager(emp_id)
    vt     = vacation_types_for_employee(emp_id)
    year   = datetime.date.today().year

    for t in vt:
        u = used_days(emp_id, t['id'], year)
        t['used_days']  = u
        t['remaining']  = (t['max_days_per_year'] - u) if t['max_days_per_year'] else None

    requests = [to_dict(r) for r in query("""
        SELECT vr.id::text, vt.name AS type_name, vt.color,
               vr.start_date, vr.end_date, vr.working_days,
               vr.status, vr.notes, vr.manager_note, vr.reviewed_at,
               (e.first_name||' '||e.last_name) AS manager_name
        FROM vacation_requests vr
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        LEFT JOIN employees e ON e.id = vr.manager_id
        WHERE vr.employee_id = %s::uuid
        ORDER BY vr.created_at DESC
    """, (emp_id,))]

    return render_template('vacation/employee.html',
                           vacation_types=vt,
                           requests=requests,
                           has_manager=bool(mgr_id),
                           year=year)


@app.route('/api/vacation/request', methods=['POST'])
@login_required
def api_vacation_submit():
    emp_id = session['employee_id']
    mgr_id = employee_solid_manager(emp_id)
    if not mgr_id:
        return jsonify({'error': 'No manager assigned — cannot submit vacation request.'}), 400

    data  = request.get_json()
    vt_id = data.get('vacation_type_id')
    start = data.get('start_date')
    end   = data.get('end_date')
    notes = (data.get('notes') or '').strip() or None

    if not vt_id or not start or not end:
        return jsonify({'error': 'vacation_type_id, start_date and end_date are required.'}), 400

    allowed = [t['id'] for t in vacation_types_for_employee(emp_id)]
    if vt_id not in allowed:
        return jsonify({'error': 'This vacation type is not available for your location.'}), 403

    start_d = datetime.date.fromisoformat(start)
    end_d   = datetime.date.fromisoformat(end)
    if end_d < start_d:
        return jsonify({'error': 'End date must be on or after start date.'}), 400

    days = sum(1 for i in range((end_d - start_d).days + 1)
               if (start_d + datetime.timedelta(i)).weekday() < 5)
    days = max(days, 1)

    vt_row = query("SELECT max_days_per_year FROM vacation_types WHERE id=%s::uuid", (vt_id,), one=True)
    if vt_row and vt_row['max_days_per_year']:
        u = used_days(emp_id, vt_id, start_d.year)
        if u + days > vt_row['max_days_per_year']:
            return jsonify({'error': f'Exceeds annual limit. Used {u}/{vt_row["max_days_per_year"]} days.'}), 400

    row = insert_returning("""
        INSERT INTO vacation_requests
          (employee_id, vacation_type_id, manager_id, start_date, end_date, working_days, notes)
        VALUES (%s::uuid,%s::uuid,%s::uuid,%s,%s,%s,%s)
        RETURNING id::text
    """, (emp_id, vt_id, mgr_id, start_d, end_d, days, notes))
    return jsonify({'ok': True, 'id': row['id'], 'working_days': days})


@app.route('/api/vacation/request/<req_id>', methods=['DELETE'])
@login_required
def api_vacation_cancel(req_id):
    emp_id = session['employee_id']
    row = query("SELECT status FROM vacation_requests WHERE id=%s::uuid AND employee_id=%s::uuid",
                (req_id, emp_id), one=True)
    if not row:
        return jsonify({'error': 'Not found'}), 404
    if row['status'] != 'PENDING':
        return jsonify({'error': 'Only PENDING requests can be cancelled.'}), 400
    execute("UPDATE vacation_requests SET status='CANCELLED', updated_at=NOW() WHERE id=%s::uuid", (req_id,))
    return jsonify({'ok': True})


# ── Manager vacation ──────────────────────────────────────────────────────────

@app.route('/vacation/team')
@require_roles(*MGMT_VACATION_ROLES)
def vacation_team():
    return render_template('vacation/team.html')


@app.route('/api/vacation/team-pending')
@require_roles(*MGMT_VACATION_ROLES)
def api_vacation_team_pending():
    mgr_id = session['employee_id']
    rows = query("""
        SELECT vr.id::text, vr.start_date, vr.end_date, vr.working_days,
               vr.notes, vr.status, vr.created_at,
               vt.name AS type_name, vt.color,
               (e.first_name||' '||e.last_name) AS employee_name,
               e.id::text AS employee_id, e.job_title,
               COALESCE(l.name,'') AS location
        FROM vacation_requests vr
        JOIN employees e ON e.id = vr.employee_id
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l ON l.id=oa.location_id
        WHERE vr.manager_id = %s::uuid AND vr.status = 'PENDING'
        ORDER BY vr.start_date
    """, (mgr_id,))
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/vacation/team-upcoming')
@require_roles(*MGMT_VACATION_ROLES)
def api_vacation_team_upcoming():
    mgr_id = session['employee_id']
    rows = query("""
        SELECT vr.id::text, vr.start_date, vr.end_date, vr.working_days,
               vr.status, vt.name AS type_name, vt.color,
               (e.first_name||' '||e.last_name) AS employee_name,
               e.id::text AS employee_id, e.job_title
        FROM vacation_requests vr
        JOIN employees e ON e.id = vr.employee_id
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        WHERE vr.manager_id = %s::uuid
          AND vr.status = 'APPROVED'
          AND vr.end_date >= CURRENT_DATE
        ORDER BY vr.start_date LIMIT 60
    """, (mgr_id,))
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/vacation/team-pending-counts')
@login_required
def api_vacation_team_pending_counts():
    mgr_id = session['employee_id']
    rows = query("""
        SELECT employee_id::text, COUNT(*)::int AS cnt
        FROM vacation_requests
        WHERE manager_id = %s::uuid AND status = 'PENDING'
        GROUP BY employee_id
    """, (mgr_id,))
    return jsonify({r['employee_id']: r['cnt'] for r in rows})


@app.route('/api/vacation/review/<req_id>', methods=['POST'])
@require_roles(*MGMT_VACATION_ROLES)
def api_vacation_review(req_id):
    data   = request.get_json()
    action = data.get('action')
    note   = (data.get('note') or '').strip() or None
    if action not in ('approve', 'reject'):
        return jsonify({'error': 'action must be approve or reject'}), 400

    mgr_id = session['employee_id']
    row = query("SELECT status FROM vacation_requests WHERE id=%s::uuid AND manager_id=%s::uuid",
                (req_id, mgr_id), one=True)
    if not row:
        return jsonify({'error': 'Not found or not your request'}), 404
    if row['status'] != 'PENDING':
        return jsonify({'error': 'Request is no longer pending'}), 400

    new_status = 'APPROVED' if action == 'approve' else 'REJECTED'
    execute("""
        UPDATE vacation_requests
        SET status=%s, manager_note=%s, reviewed_at=NOW(), updated_at=NOW()
        WHERE id=%s::uuid
    """, (new_status, note, req_id))
    return jsonify({'ok': True, 'status': new_status})
