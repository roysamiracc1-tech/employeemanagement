import json

from flask import session, redirect, url_for, request, render_template, flash, jsonify

from app import app
from app.db import query, execute, insert_returning, to_dict, get_db
from app.auth import login_required, require_roles
from app.helpers import next_employee_number, _EMP_SELECT

_ADMIN_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')

def _assign_role(user_id: str, role_name: str, company_id: str | None):
    """Insert a user_role row, preferring the company-specific role over the global one."""
    row = query("""
        SELECT id FROM roles
        WHERE name = %s AND (company_id = %s::uuid OR company_id IS NULL)
        ORDER BY company_id NULLS LAST
        LIMIT 1
    """, (role_name, company_id), one=True)
    if row:
        execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s::uuid, %s::uuid) ON CONFLICT DO NOTHING",
                (user_id, row['id']))


def seed_company_roles(company_id: str):
    """Seed ONE Company Admin role for a newly registered company.

    The COMPANY_ADMIN role gets full R/W access to every portal feature.
    Additional roles are defined by the company admin themselves.
    """
    existing = query("SELECT id FROM roles WHERE name='COMPANY_ADMIN' AND company_id=%s::uuid",
                     (company_id,), one=True)
    if existing:
        return existing['id']

    role = insert_returning(
        "INSERT INTO roles (name, description, company_id) VALUES (%s,%s,%s::uuid) RETURNING id::text",
        ('COMPANY_ADMIN', 'Company Administrator — full access to manage the company portal', company_id))

    # Grant full R/W/D on all portal features
    execute("""
        INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
        SELECT %s::uuid, id, TRUE, TRUE, TRUE FROM portal_features
        ON CONFLICT (role_id, feature_id) DO NOTHING
    """, (role['id'],))

    return role['id']


def _company_scope():
    """Return active company_id filter, or None (= no filter / all companies).
    Tech Admin: uses the manually selected context stored in session.
    Portal Admin: always scoped to their own company.
    """
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        return session.get('admin_company_id') or None
    if 'PORTAL_ADMIN' in roles:
        return session.get('company_id') or None
    return None


def _companies_with_admins():
    """Return active companies with logo_url, theme_color and their PORTAL_ADMIN/HR_ADMIN users."""
    companies = [to_dict(r) for r in query(
        "SELECT id::text, name, logo_url, theme_color FROM companies WHERE is_active ORDER BY name"
    )]
    if not companies:
        return companies
    admins = query("""
        SELECT e.company_id::text, e.first_name, e.last_name, e.job_title,
               array_agg(DISTINCT r.name ORDER BY r.name) AS roles
        FROM employees e
        JOIN users u ON u.employee_id = e.id AND u.is_active
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        WHERE r.name IN ('PORTAL_ADMIN', 'HR_ADMIN')
          AND e.employment_status = 'ACTIVE'
        GROUP BY e.company_id, e.id, e.first_name, e.last_name, e.job_title
        ORDER BY e.last_name
    """)
    admins_by_company = {}
    for a in admins:
        cid = a['company_id']
        admins_by_company.setdefault(cid, []).append({
            'name': f"{a['first_name']} {a['last_name']}",
            'job_title': a['job_title'],
            'roles': list(a['roles']),
        })
    for co in companies:
        co['admins'] = admins_by_company.get(co['id'], [])
    return companies


def _roles_for_context():
    """Return ONLY this company's custom roles for user-role assignment.
    Never return roles belonging to other companies or global template roles.
    SYSTEM_ADMIN and PORTAL_ADMIN are handled separately via _assign_role.
    """
    roles_session = session.get('roles', [])
    is_sa  = 'SYSTEM_ADMIN' in roles_session
    co_id  = session.get('admin_company_id') if is_sa else session.get('company_id')
    if not co_id:
        return []
    # Only company-specific roles (company_id = this company exactly)
    return [to_dict(r) for r in query(
        "SELECT id::text, name, description FROM roles WHERE company_id = %s::uuid ORDER BY name",
        (co_id,)
    )]


@app.route('/admin')
@require_roles(*_ADMIN_ROLES)
def admin():
    all_roles        = _roles_for_context()
    is_tech_admin    = 'SYSTEM_ADMIN' in session.get('roles', [])
    is_portal_admin  = 'PORTAL_ADMIN' in session.get('roles', [])
    companies        = []
    admin_company_id = ''
    if is_tech_admin:
        companies        = _companies_with_admins()
        admin_company_id = session.get('admin_company_id') or ''
    return render_template('admin/panel.html',
                           all_roles=all_roles,
                           is_tech_admin=is_tech_admin,
                           is_portal_admin=is_portal_admin,
                           companies=companies,
                           companies_json=json.dumps(companies),
                           admin_company_id=admin_company_id)


@app.route('/admin/register-user', methods=['GET', 'POST'])
@require_roles(*_ADMIN_ROLES)
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

        co_id = _company_scope() or request.form.get('company_id', '').strip() or None
        emp = insert_returning("""
            INSERT INTO employees
              (employee_number, first_name, last_name, email, phone_number,
               gender, job_title, employment_type, employment_status, join_date, company_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s::uuid)
            RETURNING id::text
        """, (emp_num, first_name, last_name, emp_email, phone,
              gender, job_title, emp_type, join_date or None, co_id))
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
            _assign_role(user_id, role_name, co_id)

        flash(f'Employee {first_name} {last_name} ({emp_num}) added successfully.', 'success')
        return redirect(url_for('admin'))

    co_id = _company_scope()
    co_filter     = "WHERE company_id = %s::uuid" if co_id else ""
    co_filter_and = "AND e.company_id = %s::uuid" if co_id else ""
    co_params     = (co_id,) if co_id else ()

    locations     = [to_dict(r) for r in query(f"SELECT id::text, name FROM locations {co_filter} ORDER BY name", co_params)]
    bus           = [to_dict(r) for r in query(f"SELECT id::text, name FROM business_units {co_filter} ORDER BY name", co_params)]
    fus           = [to_dict(r) for r in query(f"SELECT id::text, name, business_unit_id::text FROM functional_units {co_filter} ORDER BY name", co_params)]
    cost_centers  = [to_dict(r) for r in query("SELECT id::text, name FROM cost_centers ORDER BY name")]
    all_employees = [to_dict(r) for r in query(f"""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title
        FROM employees e WHERE e.employment_status='ACTIVE' {co_filter_and} ORDER BY e.first_name, e.last_name
    """, co_params)]
    all_roles   = _roles_for_context()
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
@require_roles(*_ADMIN_ROLES)
def api_admin_users():
    co_id = _company_scope()
    co_filter = "AND e.company_id = %s::uuid" if co_id else ""
    rows = query(f"""
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
        WHERE TRUE {co_filter}
        GROUP BY u.id, e.id, l.name
        ORDER BY e.first_name, e.last_name
    """, (co_id,) if co_id else ())
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/update-roles', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_update_roles():
    data      = request.get_json()
    if not isinstance(data, dict):
        data = {}
    user_id   = data.get('user_id')
    new_roles = data.get('roles') or []
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    if not isinstance(user_id, str):
        return jsonify({'error': 'user_id must be a string'}), 400
    if not isinstance(new_roles, list):
        return jsonify({'error': 'roles must be a list'}), 400
    co_id = _company_scope()
    if co_id:
        owner = query("SELECT 1 FROM users u JOIN employees e ON e.id=u.employee_id WHERE u.id=%s AND e.company_id=%s::uuid", (user_id, co_id), one=True)
        if not owner:
            return jsonify({'error': 'User not in your company'}), 403
        # Portal Admin cannot grant SYSTEM_ADMIN or PORTAL_ADMIN to others
        new_roles = [r for r in new_roles if r not in ('SYSTEM_ADMIN', 'PORTAL_ADMIN')]
    execute("DELETE FROM user_roles WHERE user_id = %s::uuid", (user_id,))
    for rname in new_roles:
        _assign_role(user_id, rname, co_id)
    return jsonify({'ok': True})


@app.route('/api/admin/toggle-user', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_toggle_user():
    _data = request.get_json()
    user_id = (_data if isinstance(_data, dict) else {}).get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    if not isinstance(user_id, str):
        return jsonify({'error': 'user_id must be a string'}), 400
    co_id = _company_scope()
    if co_id:
        owner = query("SELECT 1 FROM users u JOIN employees e ON e.id=u.employee_id WHERE u.id=%s AND e.company_id=%s::uuid", (user_id, co_id), one=True)
        if not owner:
            return jsonify({'error': 'User not in your company'}), 403
    execute("UPDATE users SET is_active = NOT is_active WHERE id=%s", (user_id,))
    row = query("SELECT is_active FROM users WHERE id=%s", (user_id,), one=True)
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'is_active': row['is_active']})


@app.route('/api/admin/validate-skill', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'SOLID_LINE_MANAGER', 'HR_ADMIN')
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


@app.route('/api/admin/employees')
@require_roles(*_ADMIN_ROLES)
def api_admin_employees():
    co_id = _company_scope()
    if co_id:
        sql  = _EMP_SELECT + " WHERE e.employment_status='ACTIVE' AND e.company_id=%s::uuid ORDER BY e.first_name, e.last_name"
        rows = query(sql, (co_id,))
    else:
        sql  = _EMP_SELECT + " WHERE e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name"
        rows = query(sql)
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/switch-company', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_admin_switch_company():
    company_id = (request.get_json() or {}).get('company_id') or None
    session['admin_company_id'] = company_id
    return jsonify({'ok': True, 'company_id': company_id})


@app.route('/api/admin/roles/features')
@require_roles('SYSTEM_ADMIN')
def api_admin_roles_features():
    # Global template roles only (company_id IS NULL) — these are the system-wide defaults.
    # Company-specific roles are managed via the Company Roles tab.
    roles    = [to_dict(r) for r in query(
        "SELECT id::text, name, description FROM roles WHERE company_id IS NULL ORDER BY name"
    )]
    features = [to_dict(r) for r in query(
        "SELECT id::text, code, label, description FROM portal_features ORDER BY sort_order"
    )]
    role_ids = [r['id'] for r in roles]
    access   = query(
        "SELECT role_id::text, feature_id::text, can_read, can_write, can_delete "
        "FROM role_feature_access WHERE role_id = ANY(%s::uuid[])",
        (role_ids,)
    )
    matrix = {}
    for a in access:
        rid, fid = a['role_id'], a['feature_id']
        if rid not in matrix:
            matrix[rid] = {}
        matrix[rid][fid] = {'r': bool(a['can_read']), 'w': bool(a['can_write']), 'd': bool(a['can_delete'])}
    return jsonify({'roles': roles, 'features': features, 'matrix': matrix})


@app.route('/api/admin/roles/feature-access', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_admin_update_feature_access():
    data       = request.get_json() or {}
    role_id    = data.get('role_id')
    feature_id = data.get('feature_id')
    can_read   = bool(data.get('can_read', False))
    can_write  = bool(data.get('can_write', False))
    can_delete = bool(data.get('can_delete', False))
    if not role_id or not feature_id:
        return jsonify({'error': 'role_id and feature_id required'}), 400
    execute("""
        INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s)
        ON CONFLICT (role_id, feature_id) DO UPDATE
        SET can_read=EXCLUDED.can_read, can_write=EXCLUDED.can_write, can_delete=EXCLUDED.can_delete
    """, (role_id, feature_id, can_read, can_write, can_delete))
    return jsonify({'ok': True})


# ── Company-level role feature access (PORTAL_ADMIN) ─────────────────────────

@app.route('/api/admin/company/role-feature-access')
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_role_feature_access_get():
    """Return per-company role×feature R/W/D matrix."""
    company_id = _company_scope()
    if not company_id:
        return jsonify({'error': 'No company selected'}), 400

    features = [to_dict(r) for r in query(
        "SELECT id::text, code, label FROM portal_features ORDER BY sort_order"
    )]
    # Only company-created custom roles — no global/system roles
    roles = [to_dict(r) for r in query("""
        SELECT id::text, name FROM roles
        WHERE company_id = %s::uuid
        ORDER BY name
    """, (company_id,))]

    if not roles:
        return jsonify({'company_id': company_id, 'features': features, 'roles': [], 'matrix': {}})

    # Default R/W/D per company role×feature
    global_rows = query("""
        SELECT ro.name AS role_name, pf.id::text AS feature_id,
               rfa.can_read, rfa.can_write, rfa.can_delete
        FROM role_feature_access rfa
        JOIN roles ro ON ro.id = rfa.role_id
        JOIN portal_features pf ON pf.id = rfa.feature_id
        WHERE ro.company_id = %s::uuid
    """, (company_id,))

    # Company-level R/W/D overrides
    override_rows = query("""
        SELECT ro.name AS role_name, pf.id::text AS feature_id,
               crfa.can_read, crfa.can_write, crfa.can_delete
        FROM company_role_feature_access crfa
        JOIN roles ro ON ro.id = crfa.role_id
        JOIN portal_features pf ON pf.id = crfa.feature_id
        WHERE crfa.company_id = %s::uuid
    """, (company_id,))

    global_map   = {(r['role_name'], r['feature_id']): r for r in global_rows}
    override_map = {(r['role_name'], r['feature_id']): r for r in override_rows}

    # Build matrix: {feature_id: {role_name: {r, w, d, override_r, override_w, override_d}}}
    matrix = {}
    for (rname, fid), g in global_map.items():
        if fid not in matrix:
            matrix[fid] = {}
        ov = override_map.get((rname, fid))
        matrix[fid][rname] = {
            'global_r': bool(g['can_read']),   'global_w': bool(g['can_write']),   'global_d': bool(g['can_delete']),
            'has_override': ov is not None,
            'r': bool(ov['can_read'])   if ov else bool(g['can_read']),
            'w': bool(ov['can_write'])  if ov else bool(g['can_write']),
            'd': bool(ov['can_delete']) if ov else bool(g['can_delete']),
        }

    return jsonify({
        'company_id': company_id,
        'features': features,
        'roles': roles,
        'matrix': matrix,
    })


@app.route('/api/admin/company/role-feature-access', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_role_feature_access_set():
    """Set R/W/D override for a role×feature in this company. Omit can_read/write/delete to clear override."""
    company_id = _company_scope()
    if not company_id:
        return jsonify({'error': 'No company selected'}), 400

    data       = request.get_json() or {}
    feature_id = data.get('feature_id')
    role_name  = data.get('role_name')

    if not feature_id or not role_name:
        return jsonify({'error': 'feature_id and role_name required'}), 400
    if role_name == 'SYSTEM_ADMIN':
        return jsonify({'error': 'Cannot manage SYSTEM_ADMIN role'}), 403

    role_row = query("""
        SELECT id::text FROM roles
        WHERE name = %s AND (company_id = %s::uuid OR company_id IS NULL)
        ORDER BY company_id NULLS LAST LIMIT 1
    """, (role_name, company_id), one=True)
    if not role_row:
        return jsonify({'error': 'Role not found'}), 400

    # None means clear override (revert to global default)
    if data.get('clear'):
        execute("""
            DELETE FROM company_role_feature_access
            WHERE company_id=%s::uuid AND role_id=%s::uuid AND feature_id=%s::uuid
        """, (company_id, role_row['id'], feature_id))
    else:
        can_read   = bool(data.get('r', False))
        can_write  = bool(data.get('w', False))
        can_delete = bool(data.get('d', False))
        execute("""
            INSERT INTO company_role_feature_access
                (company_id, role_id, feature_id, can_read, can_write, can_delete, updated_by, updated_at)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s::uuid, NOW())
            ON CONFLICT (company_id, role_id, feature_id) DO UPDATE
            SET can_read=EXCLUDED.can_read, can_write=EXCLUDED.can_write,
                can_delete=EXCLUDED.can_delete, updated_by=EXCLUDED.updated_by, updated_at=NOW()
        """, (company_id, role_row['id'], feature_id, can_read, can_write, can_delete, session['user_id']))

    return jsonify({'ok': True})


# ── Company Role CRUD (PORTAL_ADMIN manages their company's roles) ────────────

@app.route('/api/admin/company/roles')
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_roles_list():
    company_id = _company_scope()
    if not company_id:
        return jsonify({'error': 'No company selected'}), 400
    # Only show custom roles created by the company — NOT global system roles (PORTAL_ADMIN etc.)
    rows = query("""
        SELECT r.id::text, r.name, r.description,
               COUNT(ur.user_id)::int AS user_count
        FROM roles r
        LEFT JOIN user_roles ur ON ur.role_id = r.id
        WHERE r.company_id = %s::uuid
        GROUP BY r.id, r.name, r.description
        ORDER BY r.name
    """, (company_id,))
    features = [to_dict(f) for f in query(
        "SELECT id::text, code, label FROM portal_features ORDER BY sort_order"
    )]
    access = query("""
        SELECT rfa.role_id::text, pf.code, rfa.can_read, rfa.can_write, rfa.can_delete
        FROM role_feature_access rfa
        JOIN roles r ON r.id = rfa.role_id
        JOIN portal_features pf ON pf.id = rfa.feature_id
        WHERE r.company_id = %s::uuid
    """, (company_id,))
    perms = {}
    for a in access:
        perms.setdefault(a['role_id'], {})[a['code']] = {
            'r': bool(a['can_read']), 'w': bool(a['can_write']), 'd': bool(a['can_delete'])
        }
    return jsonify({
        'roles': [to_dict(r) for r in rows],
        'features': features,
        'perms': perms,
        'company_id': company_id,
    })


@app.route('/api/admin/company/roles', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_roles_create():
    company_id = _company_scope()
    if not company_id:
        return jsonify({'error': 'No company selected'}), 400
    data = request.get_json() or {}
    raw_name = data.get('name')
    if not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name = raw_name.strip().upper().replace(' ', '_')
    raw_desc = data.get('description')
    desc = (str(raw_desc).strip() if isinstance(raw_desc, str) else None) or None
    if not name:
        return jsonify({'error': 'name required'}), 400
    if query("SELECT 1 FROM roles WHERE name=%s AND company_id=%s::uuid", (name, company_id), one=True):
        return jsonify({'error': f'Role "{name}" already exists'}), 409
    row = insert_returning(
        "INSERT INTO roles (name, description, company_id) VALUES (%s,%s,%s::uuid) RETURNING id::text",
        (name, desc, company_id))
    return jsonify({'id': row['id'], 'name': name}), 201


@app.route('/api/admin/company/roles/<role_id>', methods=['PUT'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_roles_update(role_id):
    company_id = _company_scope()
    role = query("SELECT id, name, company_id FROM roles WHERE id=%s::uuid", (role_id,), one=True)
    if not role or (role['company_id'] and str(role['company_id']) != company_id):
        return jsonify({'error': 'Role not found'}), 404
    if role['company_id'] is None:
        return jsonify({'error': 'Cannot rename system roles'}), 403
    data = request.get_json() or {}
    raw_name = data.get('name')
    if raw_name is not None and not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name = (raw_name or '').strip().upper().replace(' ', '_')
    raw_desc = data.get('description')
    desc = (str(raw_desc).strip() if isinstance(raw_desc, str) else None) or None
    if not name:
        return jsonify({'error': 'name required'}), 400
    execute("UPDATE roles SET name=%s, description=%s WHERE id=%s::uuid", (name, desc, role_id))
    return jsonify({'ok': True})


@app.route('/api/admin/company/roles/<role_id>', methods=['DELETE'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_roles_delete(role_id):
    company_id = _company_scope()
    role = query("SELECT id, name, company_id, (SELECT COUNT(*) FROM user_roles WHERE role_id=roles.id) AS cnt FROM roles WHERE id=%s::uuid", (role_id,), one=True)
    if not role or (role['company_id'] and str(role['company_id']) != company_id):
        return jsonify({'error': 'Role not found'}), 404
    if role['company_id'] is None:
        return jsonify({'error': 'Cannot delete system roles'}), 403
    if role['cnt'] and int(role['cnt']) > 0:
        return jsonify({'error': f'Cannot delete — {role["cnt"]} user(s) have this role'}), 409
    execute("DELETE FROM roles WHERE id=%s::uuid", (role_id,))
    return jsonify({'ok': True})


@app.route('/api/admin/company/roles/<role_id>/permissions', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN')
def api_company_role_set_permissions(role_id):
    """Set all feature permissions for a company role at once."""
    company_id = _company_scope()
    role = query("SELECT id, company_id FROM roles WHERE id=%s::uuid", (role_id,), one=True)
    if not role or (role['company_id'] and str(role['company_id']) != company_id):
        return jsonify({'error': 'Role not found'}), 404
    data = request.get_json() or {}
    # data = {feature_id: {can_read, can_write, can_delete}, ...}
    for feature_id, perms in data.items():
        execute("""
            INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            ON CONFLICT (role_id, feature_id) DO UPDATE
            SET can_read=EXCLUDED.can_read, can_write=EXCLUDED.can_write, can_delete=EXCLUDED.can_delete
        """, (role_id, feature_id,
              bool(perms.get('r', False)),
              bool(perms.get('w', False)),
              bool(perms.get('d', False))))
    return jsonify({'ok': True})


@app.route('/api/admin/company/seed-admin-user', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_seed_company_admin_user():
    """SA creates the first Portal Admin user for a company."""
    data       = request.get_json() or {}
    company_id = data.get('company_id')
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    email      = (data.get('email') or '').strip().lower()
    emp_num    = (data.get('employee_number') or '').strip()

    if not all([company_id, first_name, last_name, email, emp_num]):
        return jsonify({'error': 'company_id, first_name, last_name, email, employee_number required'}), 400
    if query("SELECT 1 FROM users WHERE LOWER(email)=%s", (email,), one=True):
        return jsonify({'error': 'Email already registered'}), 409

    emp = insert_returning("""
        INSERT INTO employees (employee_number, first_name, last_name, email,
                               employment_status, company_id)
        VALUES (%s, %s, %s, %s, 'ACTIVE', %s::uuid) RETURNING id::text
    """, (emp_num, first_name, last_name, email, company_id))

    user = insert_returning("""
        INSERT INTO users (employee_id, email, username, is_active)
        VALUES (%s::uuid, %s, %s, TRUE) RETURNING id::text
    """, (emp['id'], email, email.split('@')[0]))

    # Assign PORTAL_ADMIN (global system role)
    execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT %s::uuid, id FROM roles WHERE name='PORTAL_ADMIN' AND company_id IS NULL
        ON CONFLICT DO NOTHING
    """, (user['id'],))

    return jsonify({'ok': True, 'user_id': user['id'], 'employee_id': emp['id']})


@app.route('/api/admin/org/business-units')
@require_roles(*_ADMIN_ROLES)
def api_org_bus():
    co_id = _company_scope()
    co_where = "WHERE bu.company_id = %s::uuid" if co_id else ""
    rows = query(f"""
        SELECT bu.id::text, bu.name, bu.code, bu.description,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM business_units bu
        LEFT JOIN employee_org_assignments oa ON oa.business_unit_id=bu.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        {co_where}
        GROUP BY bu.id, bu.name, bu.code, bu.description ORDER BY bu.name
    """, (co_id,) if co_id else ())
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/org/locations')
@require_roles(*_ADMIN_ROLES)
def api_org_locs():
    co_id = _company_scope()
    co_where = "WHERE l.company_id = %s::uuid" if co_id else ""
    rows = query(f"""
        SELECT l.id::text, l.name, l.office_code, l.city, l.country,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM locations l
        LEFT JOIN employee_org_assignments oa ON oa.location_id=l.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        {co_where}
        GROUP BY l.id, l.name, l.office_code, l.city, l.country ORDER BY l.name
    """, (co_id,) if co_id else ())
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/org/functional-units')
@require_roles(*_ADMIN_ROLES)
def api_org_fus():
    co_id = _company_scope()
    co_where = "WHERE fu.company_id = %s::uuid" if co_id else ""
    rows = query(f"""
        SELECT fu.id::text, fu.name, fu.code, fu.description,
               fu.business_unit_id::text, bu.name AS bu_name,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM functional_units fu
        LEFT JOIN business_units bu ON bu.id=fu.business_unit_id
        LEFT JOIN employee_org_assignments oa ON oa.functional_unit_id=fu.id AND oa.is_current
        LEFT JOIN employees e ON e.id=oa.employee_id AND e.employment_status='ACTIVE'
        {co_where}
        GROUP BY fu.id, fu.name, fu.code, fu.description, fu.business_unit_id, bu.name
        ORDER BY bu.name, fu.name
    """, (co_id,) if co_id else ())
    return jsonify([to_dict(r) for r in rows])


# ── Business Unit CRUD ────────────────────────────────────────────────────────

def _assert_org_ownership(table, id_col, record_id):
    """Return 403 response if Portal Admin does not own this record, else None."""
    co_id = _company_scope()
    if not co_id:
        return None
    row = query(f"SELECT 1 FROM {table} WHERE {id_col}=%s::uuid AND company_id=%s::uuid", (record_id, co_id), one=True)
    if not row:
        return jsonify({'error': 'Record not found or not in your company'}), 403
    return None


@app.route('/api/admin/org/business-units', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_org_bu_create():
    data  = request.get_json() or {}
    raw_name = data.get('name')
    if raw_name is not None and not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name  = (raw_name or '').strip()
    code  = str(data.get('code') or '').strip() or None if isinstance(data.get('code'), str) else None
    desc  = str(data.get('description') or '').strip() or None if isinstance(data.get('description'), str) else None
    co_id = _company_scope()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if code and query("SELECT 1 FROM business_units WHERE code=%s", (code,), one=True):
        return jsonify({'error': f'Code "{code}" is already in use'}), 409
    row = insert_returning(
        "INSERT INTO business_units (name, code, description, company_id) VALUES (%s,%s,%s,%s::uuid) RETURNING id::text",
        (name, code, desc, co_id),
    )
    return jsonify({'ok': True, 'id': row['id']})


@app.route('/api/admin/org/business-units/<bu_id>', methods=['PUT'])
@require_roles(*_ADMIN_ROLES)
def api_org_bu_update(bu_id):
    err = _assert_org_ownership('business_units', 'id', bu_id)
    if err:
        return err
    data = request.get_json() or {}
    raw_name = data.get('name')
    if raw_name is not None and not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name = (raw_name or '').strip()
    raw_code = data.get('code')
    code = (str(raw_code).strip() or None) if isinstance(raw_code, str) else None
    raw_desc = data.get('description')
    desc = (str(raw_desc).strip() or None) if isinstance(raw_desc, str) else None
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if code:
        conflict = query("SELECT 1 FROM business_units WHERE code=%s AND id!=%s::uuid", (code, bu_id), one=True)
        if conflict:
            return jsonify({'error': f'Code "{code}" is already in use'}), 409
    execute("UPDATE business_units SET name=%s, code=%s, description=%s WHERE id=%s::uuid",
            (name, code, desc, bu_id))
    return jsonify({'ok': True})


@app.route('/api/admin/org/business-units/<bu_id>', methods=['DELETE'])
@require_roles(*_ADMIN_ROLES)
def api_org_bu_delete(bu_id):
    err = _assert_org_ownership('business_units', 'id', bu_id)
    if err:
        return err
    row = query(
        "SELECT COUNT(*) AS c FROM employee_org_assignments WHERE business_unit_id=%s::uuid AND is_current",
        (bu_id,), one=True,
    )
    count = row['c'] if row else 0
    if count:
        return jsonify({'error': f'Cannot delete — {count} employee(s) currently assigned to this BU'}), 409
    execute("DELETE FROM business_units WHERE id=%s::uuid", (bu_id,))
    return jsonify({'ok': True})


# ── Location CRUD ─────────────────────────────────────────────────────────────

@app.route('/api/admin/org/locations', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_org_loc_create():
    data        = request.get_json() or {}
    raw_name    = data.get('name')
    if raw_name is not None and not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name        = (raw_name or '').strip()
    office_code = (data.get('office_code') or '').strip() or None if isinstance(data.get('office_code', ''), str) else None
    country     = (data.get('country') or '').strip() or None if isinstance(data.get('country', ''), str) else None
    city        = (data.get('city') or '').strip() or None if isinstance(data.get('city', ''), str) else None
    co_id       = _company_scope()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if office_code and query("SELECT 1 FROM locations WHERE office_code=%s", (office_code,), one=True):
        return jsonify({'error': f'Office code "{office_code}" is already in use'}), 409
    row = insert_returning(
        "INSERT INTO locations (name, office_code, country, city, company_id) VALUES (%s,%s,%s,%s,%s::uuid) RETURNING id::text",
        (name, office_code, country, city, co_id),
    )
    return jsonify({'ok': True, 'id': row['id']})


@app.route('/api/admin/org/locations/<loc_id>', methods=['PUT'])
@require_roles(*_ADMIN_ROLES)
def api_org_loc_update(loc_id):
    err = _assert_org_ownership('locations', 'id', loc_id)
    if err:
        return err
    data        = request.get_json() or {}
    raw_name    = data.get('name')
    if raw_name is not None and not isinstance(raw_name, str):
        return jsonify({'error': 'name must be a string'}), 400
    name        = (raw_name or '').strip()
    raw_oc      = data.get('office_code')
    office_code = (str(raw_oc).strip() or None) if isinstance(raw_oc, str) else None
    raw_country = data.get('country')
    country     = (str(raw_country).strip() or None) if isinstance(raw_country, str) else None
    raw_city    = data.get('city')
    city        = (str(raw_city).strip() or None) if isinstance(raw_city, str) else None
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if office_code:
        conflict = query("SELECT 1 FROM locations WHERE office_code=%s AND id!=%s::uuid", (office_code, loc_id), one=True)
        if conflict:
            return jsonify({'error': f'Office code "{office_code}" is already in use'}), 409
    execute("UPDATE locations SET name=%s, office_code=%s, country=%s, city=%s WHERE id=%s::uuid",
            (name, office_code, country, city, loc_id))
    return jsonify({'ok': True})


@app.route('/api/admin/org/locations/<loc_id>', methods=['DELETE'])
@require_roles(*_ADMIN_ROLES)
def api_org_loc_delete(loc_id):
    err = _assert_org_ownership('locations', 'id', loc_id)
    if err:
        return err
    row = query(
        "SELECT COUNT(*) AS c FROM employee_org_assignments WHERE location_id=%s::uuid AND is_current",
        (loc_id,), one=True,
    )
    count = row['c'] if row else 0
    if count:
        return jsonify({'error': f'Cannot delete — {count} employee(s) currently assigned to this location'}), 409
    execute("DELETE FROM locations WHERE id=%s::uuid", (loc_id,))
    return jsonify({'ok': True})


# ── Functional Unit CRUD ──────────────────────────────────────────────────────

@app.route('/api/admin/org/functional-units', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_org_fu_create():
    data  = request.get_json()
    name  = (data.get('name') or '').strip()
    code  = (data.get('code') or '').strip() or None
    desc  = (data.get('description') or '').strip() or None
    bu_id = (data.get('business_unit_id') or '').strip() or None
    co_id = _company_scope()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if code and query("SELECT 1 FROM functional_units WHERE code=%s", (code,), one=True):
        return jsonify({'error': f'Code "{code}" is already in use'}), 409
    row = insert_returning(
        "INSERT INTO functional_units (name, code, description, business_unit_id, company_id) VALUES (%s,%s,%s,%s::uuid,%s::uuid) RETURNING id::text",
        (name, code, desc, bu_id, co_id),
    )
    return jsonify({'ok': True, 'id': row['id']})


@app.route('/api/admin/org/functional-units/<fu_id>', methods=['PUT'])
@require_roles(*_ADMIN_ROLES)
def api_org_fu_update(fu_id):
    err = _assert_org_ownership('functional_units', 'id', fu_id)
    if err:
        return err
    data  = request.get_json()
    name  = (data.get('name') or '').strip()
    code  = (data.get('code') or '').strip() or None
    desc  = (data.get('description') or '').strip() or None
    bu_id = (data.get('business_unit_id') or '').strip() or None
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if code:
        conflict = query("SELECT 1 FROM functional_units WHERE code=%s AND id!=%s::uuid", (code, fu_id), one=True)
        if conflict:
            return jsonify({'error': f'Code "{code}" is already in use'}), 409
    execute("UPDATE functional_units SET name=%s, code=%s, description=%s, business_unit_id=%s::uuid WHERE id=%s::uuid",
            (name, code, desc, bu_id, fu_id))
    return jsonify({'ok': True})


@app.route('/api/admin/org/functional-units/<fu_id>', methods=['DELETE'])
@require_roles(*_ADMIN_ROLES)
def api_org_fu_delete(fu_id):
    err = _assert_org_ownership('functional_units', 'id', fu_id)
    if err:
        return err
    count = query(
        "SELECT COUNT(*) AS c FROM employee_org_assignments WHERE functional_unit_id=%s::uuid AND is_current",
        (fu_id,), one=True,
    )['c']
    if count:
        return jsonify({'error': f'Cannot delete — {count} employee(s) currently assigned to this FU'}), 409
    execute("DELETE FROM functional_units WHERE id=%s::uuid", (fu_id,))
    return jsonify({'ok': True})
