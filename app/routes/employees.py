from flask import session, redirect, url_for, request, render_template, flash, jsonify

from app import app
from app.db import query, execute, insert_returning, to_dict
from app.auth import login_required, require_roles
from app.helpers import fetch_employees, direct_report_ids, is_direct_report


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route('/directory')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER')
def directory():
    departments = [to_dict(r) for r in query("SELECT id::text, name, code FROM business_units ORDER BY name")]
    locations   = [to_dict(r) for r in query("SELECT id::text, name, office_code FROM locations ORDER BY name")]
    return render_template('employees/directory.html',
                           departments=departments, locations=locations)


@app.route('/my-team')
@require_roles('SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def my_team():
    return render_template('employees/my_team.html')


@app.route('/profile')
@app.route('/profile/<emp_id>')
@login_required
def profile(emp_id=None):
    if emp_id is None:
        emp_id = session['employee_id']

    roles   = session.get('roles', [])
    current = session['employee_id']

    if emp_id != current:
        if any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']):
            pass
        elif 'SOLID_LINE_MANAGER' in roles:
            if not is_direct_report(current, emp_id):
                flash('You do not have permission to view this profile.', 'error')
                return redirect(url_for('my_team'))
        else:
            flash('You can only view your own profile.', 'error')
            return redirect(url_for('dashboard'))

    rows = fetch_employees(emp_ids=[emp_id])
    if not rows:
        flash('Employee not found.', 'error')
        return redirect(url_for('dashboard'))

    emp  = rows[0]
    team = []
    if 'SOLID_LINE_MANAGER' in roles and emp_id == current:
        ids = direct_report_ids(current)
        if ids:
            team = fetch_employees(emp_ids=ids)

    is_own      = (emp_id == current)
    all_skills  = [to_dict(r) for r in query("SELECT id::text, name FROM skills ORDER BY name")]
    prof_levels = [to_dict(r) for r in query("SELECT id::text, level_name, level_order FROM proficiency_levels ORDER BY level_order")]
    all_certs   = [to_dict(r) for r in query("SELECT id::text, name, provider FROM certifications ORDER BY name")]

    return render_template('employees/profile.html',
                           emp=emp, team=team, is_own=is_own,
                           all_skills=all_skills,
                           prof_levels=prof_levels,
                           all_certs=all_certs)


# ── Employee APIs ─────────────────────────────────────────────────────────────

@app.route('/api/employees')
@login_required
def api_employees():
    roles = session.get('roles', [])
    if any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER']):
        data = fetch_employees()
    elif any(r in roles for r in ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']):
        ids  = direct_report_ids(session['employee_id'])
        data = fetch_employees(emp_ids=ids)
    else:
        data = fetch_employees(emp_ids=[session['employee_id']])
    return jsonify(data)


@app.route('/api/my-team')
@require_roles('SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def api_my_team():
    ids = direct_report_ids(session['employee_id'])
    return jsonify(fetch_employees(emp_ids=ids))


# ── Profile self-edit APIs ────────────────────────────────────────────────────

@app.route('/api/user/theme', methods=['POST'])
@login_required
def api_user_theme():
    pref = (request.get_json() or {}).get('theme', 'light')
    if pref not in ('light', 'dark'):
        return jsonify({'error': 'Invalid theme'}), 400
    execute("UPDATE users SET theme_preference=%s WHERE id=%s", (pref, session['user_id']))
    session['theme_pref'] = pref
    return jsonify({'ok': True, 'theme': pref})


@app.route('/api/profile/gender', methods=['POST'])
@login_required
def api_profile_gender():
    gender = (request.get_json().get('gender') or '').strip().upper() or None
    if gender and gender not in ('MALE', 'FEMALE', 'OTHER'):
        return jsonify({'error': 'Invalid gender value'}), 400
    execute("UPDATE employees SET gender=%s WHERE id=%s::uuid",
            (gender, session['employee_id']))
    return jsonify({'ok': True})


@app.route('/api/profile/skills', methods=['POST'])
@login_required
def api_profile_skill_save():
    data       = request.get_json()
    emp_id     = session['employee_id']
    skill_id   = data.get('skill_id')
    level_id   = data.get('level_id') or None
    is_primary = bool(data.get('is_primary', False))
    if not skill_id:
        return jsonify({'error': 'skill_id required'}), 400
    execute("""
        INSERT INTO employee_skills
          (employee_id, skill_id, self_rating_level_id, is_primary_skill, validation_status)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s, 'SELF_ASSESSED')
        ON CONFLICT (employee_id, skill_id) DO UPDATE
          SET self_rating_level_id = EXCLUDED.self_rating_level_id,
              is_primary_skill     = EXCLUDED.is_primary_skill,
              validation_status    = CASE
                WHEN employee_skills.manager_validated_level_id IS NOT NULL
                THEN employee_skills.validation_status
                ELSE 'SELF_ASSESSED' END,
              updated_at = NOW()
    """, (emp_id, skill_id, level_id, is_primary))
    return jsonify({'ok': True})


@app.route('/api/profile/skills/<skill_id>', methods=['DELETE'])
@login_required
def api_profile_skill_delete(skill_id):
    execute("DELETE FROM employee_skills WHERE employee_id=%s::uuid AND skill_id=%s::uuid",
            (session['employee_id'], skill_id))
    return jsonify({'ok': True})


@app.route('/api/profile/certifications', methods=['POST'])
@login_required
def api_profile_cert_add():
    data    = request.get_json()
    emp_id  = session['employee_id']
    cert_id = data.get('cert_id')
    if not cert_id:
        return jsonify({'error': 'cert_id required'}), 400
    row = insert_returning("""
        INSERT INTO employee_certifications
          (employee_id, certification_id, issued_date, expiry_date, certificate_url, verification_status)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, 'UNVERIFIED')
        RETURNING id::text
    """, (emp_id, cert_id,
          data.get('issued_date') or None,
          data.get('expiry_date') or None,
          data.get('certificate_url') or None))
    return jsonify({'ok': True, 'id': row['id']})


@app.route('/api/profile/certifications/<ec_id>', methods=['PUT'])
@login_required
def api_profile_cert_update(ec_id):
    data = request.get_json()
    execute("""
        UPDATE employee_certifications
        SET issued_date=%s, expiry_date=%s, certificate_url=%s
        WHERE id=%s::uuid AND employee_id=%s::uuid
    """, (data.get('issued_date') or None,
          data.get('expiry_date') or None,
          data.get('certificate_url') or None,
          ec_id, session['employee_id']))
    return jsonify({'ok': True})


@app.route('/api/profile/certifications/<ec_id>', methods=['DELETE'])
@login_required
def api_profile_cert_delete(ec_id):
    execute("DELETE FROM employee_certifications WHERE id=%s::uuid AND employee_id=%s::uuid",
            (ec_id, session['employee_id']))
    return jsonify({'ok': True})
