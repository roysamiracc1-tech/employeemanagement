from flask import session, redirect, url_for, request, render_template, flash, jsonify

from app import app
from app.db import query, execute, insert_returning, to_dict, get_db
from app.auth import login_required, require_roles
from app.helpers import next_employee_number


@app.route('/admin')
@require_roles('SYSTEM_ADMIN')
def admin():
    all_roles = [to_dict(r) for r in query("SELECT id::text, name, description FROM roles ORDER BY name")]
    return render_template('admin/panel.html', all_roles=all_roles)


@app.route('/admin/register-user', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_register_user():
    if request.method == 'POST':
        first_name    = request.form.get('first_name', '').strip()
        last_name     = request.form.get('last_name', '').strip()
        emp_email     = request.form.get('emp_email', '').strip().lower()
        phone         = request.form.get('phone', '').strip() or None
        gender        = request.form.get('gender', '').strip() or None
        job_title     = request.form.get('job_title', '').strip() or None
        emp_type      = request.form.get('employment_type', '').strip() or None
        join_date     = request.form.get('join_date', '').strip() or None
        emp_num       = request.form.get('employee_number', '').strip()
        location_id   = request.form.get('location_id', '').strip() or None
        bu_id         = request.form.get('business_unit_id', '').strip() or None
        fu_id         = request.form.get('functional_unit_id', '').strip() or None
        cc_id         = request.form.get('cost_center_id', '').strip() or None
        solid_mgr_id  = request.form.get('solid_manager_id', '').strip() or None
        dotted_mgr_id = request.form.get('dotted_manager_id', '').strip() or None
        username      = request.form.get('username', '').strip()
        roles_list    = request.form.getlist('roles')

        errors = []
        if not first_name or not last_name:
            errors.append('First and last name are required.')
        if not emp_email:
            errors.append('Work email is required.')
        if not emp_num:
            errors.append('Employee number is required.')
        if not username:
            errors.append('Username is required.')
        if query("SELECT 1 FROM employees WHERE LOWER(email) = %s", (emp_email,), one=True):
            errors.append(f'Email {emp_email} is already in use.')
        if query("SELECT 1 FROM employees WHERE employee_number = %s", (emp_num,), one=True):
            errors.append(f'Employee number {emp_num} is already taken.')
        if query("SELECT 1 FROM users WHERE username = %s", (username,), one=True):
            errors.append(f'Username "{username}" is already taken.')
        if query("SELECT 1 FROM users WHERE LOWER(email) = %s", (emp_email,), one=True):
            errors.append('A portal account with that email already exists.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return redirect(url_for('admin_register_user'))

        emp = insert_returning("""
            INSERT INTO employees
              (employee_number, first_name, last_name, email, phone_number,
               gender, job_title, employment_type, employment_status, join_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s)
            RETURNING id::text
        """, (emp_num, first_name, last_name, emp_email, phone,
              gender, job_title, emp_type, join_date or None))
        emp_id = emp['id']

        if any([location_id, bu_id, fu_id, cc_id]):
            execute("""
                INSERT INTO employee_org_assignments
                  (employee_id, location_id, business_unit_id, functional_unit_id, cost_center_id, is_current)
                VALUES (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,TRUE)
            """, (emp_id, location_id, bu_id, fu_id, cc_id))

        if solid_mgr_id:
            execute("""
                INSERT INTO manager_relationships (employee_id, manager_id, relationship_type)
                VALUES (%s::uuid,%s::uuid,'SOLID_LINE') ON CONFLICT DO NOTHING
            """, (emp_id, solid_mgr_id))
        if dotted_mgr_id and dotted_mgr_id != solid_mgr_id:
            execute("""
                INSERT INTO manager_relationships (employee_id, manager_id, relationship_type)
                VALUES (%s::uuid,%s::uuid,'DOTTED_LINE') ON CONFLICT DO NOTHING
            """, (emp_id, dotted_mgr_id))

        skill_ids     = request.form.getlist('skill_id')
        skill_levels  = request.form.getlist('skill_level_id')
        skill_primary = request.form.getlist('skill_primary')
        for i, sid in enumerate(skill_ids):
            if not sid:
                continue
            level_id   = skill_levels[i] if i < len(skill_levels) else None
            is_primary = str(i) in skill_primary
            execute("""
                INSERT INTO employee_skills
                  (employee_id, skill_id, self_rating_level_id, is_primary_skill, validation_status)
                VALUES (%s::uuid,%s::uuid,%s::uuid,%s,'SELF_ASSESSED')
                ON CONFLICT (employee_id, skill_id) DO NOTHING
            """, (emp_id, sid, level_id or None, is_primary))

        user = insert_returning("""
            INSERT INTO users (employee_id, email, username, is_active)
            VALUES (%s::uuid,%s,%s,TRUE) RETURNING id::text
        """, (emp_id, emp_email, username))
        user_id = user['id']

        for role_name in set(roles_list) | {'EMPLOYEE'}:
            execute("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s::uuid, id FROM roles WHERE name=%s
                ON CONFLICT DO NOTHING
            """, (user_id, role_name))

        flash(f'Employee {first_name} {last_name} ({emp_num}) added successfully.', 'success')
        return redirect(url_for('admin'))

    locations     = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]
    bus           = [to_dict(r) for r in query("SELECT id::text, name FROM business_units ORDER BY name")]
    fus           = [to_dict(r) for r in query("SELECT id::text, name, business_unit_id::text FROM functional_units ORDER BY name")]
    cost_centers  = [to_dict(r) for r in query("SELECT id::text, name FROM cost_centers ORDER BY name")]
    all_employees = [to_dict(r) for r in query("""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title
        FROM employees e WHERE e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name
    """)]
    all_roles   = [to_dict(r) for r in query("SELECT id::text, name, description FROM roles ORDER BY name")]
    all_skills  = [to_dict(r) for r in query("SELECT id::text, name FROM skills ORDER BY name")]
    prof_levels = [to_dict(r) for r in query("SELECT id::text, level_name, level_order FROM proficiency_levels ORDER BY level_order")]

    return render_template('admin/register.html',
                           locations=locations, bus=bus, fus=fus,
                           cost_centers=cost_centers,
                           all_employees=all_employees,
                           all_roles=all_roles,
                           all_skills=all_skills,
                           prof_levels=prof_levels,
                           next_emp_num=next_employee_number())


# ── Admin APIs ────────────────────────────────────────────────────────────────

@app.route('/api/admin/users')
@require_roles('SYSTEM_ADMIN')
def api_admin_users():
    rows = query("""
        SELECT u.id::text, u.username, u.email, u.is_active, u.last_login_at,
               e.employee_number, e.first_name, e.last_name, e.job_title,
               e.id::text AS employee_id, e.employment_status,
               COALESCE(l.name,'') AS location,
               ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
        FROM users u
        JOIN employees e ON e.id = u.employee_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l ON l.id=oa.location_id
        LEFT JOIN user_roles ur ON ur.user_id=u.id
        LEFT JOIN roles r ON r.id=ur.role_id
        GROUP BY u.id, e.id, l.name
        ORDER BY e.first_name, e.last_name
    """)
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/update-roles', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_update_roles():
    data      = request.get_json()
    user_id   = data.get('user_id')
    new_roles = data.get('roles', [])
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    db = get_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        for rname in new_roles:
            cur.execute("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s, id FROM roles WHERE name = %s ON CONFLICT DO NOTHING
            """, (user_id, rname))
    db.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/toggle-user', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_toggle_user():
    user_id = request.get_json().get('user_id')
    execute("UPDATE users SET is_active = NOT is_active WHERE id=%s", (user_id,))
    row = query("SELECT is_active FROM users WHERE id=%s", (user_id,), one=True)
    return jsonify({'is_active': row['is_active']})


@app.route('/api/admin/validate-skill', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'SOLID_LINE_MANAGER', 'HR_ADMIN')
def api_validate_skill():
    data = request.get_json()
    execute("""
        UPDATE employee_skills
        SET validation_status = %s,
            manager_validated_level_id = (SELECT id FROM proficiency_levels WHERE level_name = %s),
            updated_at = NOW()
        WHERE id = %s
    """, (data.get('status', 'VALIDATED'), data.get('level'), data.get('skill_id')))
    return jsonify({'ok': True})


@app.route('/api/admin/org/business-units')
@require_roles('SYSTEM_ADMIN')
def api_org_bus():
    rows = query("""
        SELECT bu.id::text, bu.name, bu.code,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM business_units bu
        LEFT JOIN employee_org_assignments oa ON oa.business_unit_id=bu.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        GROUP BY bu.id, bu.name, bu.code ORDER BY bu.name
    """)
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/org/locations')
@require_roles('SYSTEM_ADMIN')
def api_org_locs():
    rows = query("""
        SELECT l.id::text, l.name, l.office_code,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM locations l
        LEFT JOIN employee_org_assignments oa ON oa.location_id=l.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        GROUP BY l.id, l.name, l.office_code ORDER BY l.name
    """)
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/org/functional-units')
@require_roles('SYSTEM_ADMIN')
def api_org_fus():
    rows = query("""
        SELECT fu.id::text, fu.name, fu.code, bu.name AS bu_name,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM functional_units fu
        LEFT JOIN business_units bu ON bu.id=fu.business_unit_id
        LEFT JOIN employee_org_assignments oa ON oa.functional_unit_id=fu.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        GROUP BY fu.id, fu.name, fu.code, bu.name ORDER BY bu.name, fu.name
    """)
    return jsonify([to_dict(r) for r in rows])
