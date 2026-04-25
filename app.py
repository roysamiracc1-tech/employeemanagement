import os
import datetime
from functools import wraps

import psycopg2
import psycopg2.extras
from flask import (Flask, g, session, redirect, url_for, request,
                   render_template, jsonify, flash)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hr-portal-dev-secret-2024')
app.permanent_session_lifetime = datetime.timedelta(hours=8)

DB_CONFIG = {
    'host':   os.getenv('PGHOST',     'localhost'),
    'port':   int(os.getenv('PGPORT', 5432)),
    'dbname': os.getenv('PGDATABASE', 'employee'),
    'user':   os.getenv('PGUSER',     'samirroy'),
    'password': os.getenv('PGPASSWORD') or None,
}

# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop('db', None)
    if db:
        db.close()

def query(sql, params=(), one=False):
    with get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()

def execute(sql, params=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
    db.commit()

def serialize(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v

def to_dict(row):
    return {k: serialize(v) for k, v in dict(row).items()}

# ─── Auth decorators ───────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if not any(r in session.get('roles', []) for r in roles):
                flash('You do not have access to that page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.context_processor
def inject_ctx():
    def has_role(*roles):
        return any(r in session.get('roles', []) for r in roles)
    return dict(has_role=has_role, session=session, request=request, now=datetime.datetime.now)

# ─── Core employee query ───────────────────────────────────────────────────────

_EMP_SELECT = """
    SELECT
        e.id::text,
        e.employee_number,
        e.first_name || ' ' || e.last_name       AS full_name,
        e.first_name,
        e.last_name,
        e.email,
        COALESCE(e.phone_number, '')              AS phone_number,
        COALESCE(e.job_title, '')                 AS job_title,
        e.employment_status,
        COALESCE(e.employment_type, '')           AS employment_type,
        e.join_date,
        COALESCE(l.name, '')                      AS location,
        COALESCE(l.office_code, '')               AS office_code,
        COALESCE(bu.name, '')                     AS business_unit,
        COALESCE(bu.code, '')                     AS bu_code,
        COALESCE(fu.name, '')                     AS functional_unit,
        COALESCE(fu.code, '')                     AS fu_code,
        COALESCE(cc.name, '')                     AS cost_center,
        COALESCE(sm_e.first_name || ' ' || sm_e.last_name, '') AS solid_manager_name,
        COALESCE(sm_e.job_title, '')              AS solid_manager_title,
        sm_e.id::text                             AS solid_manager_id,
        COALESCE(dm_e.first_name || ' ' || dm_e.last_name, '') AS dotted_manager_name,
        COALESCE(dm_e.job_title, '')              AS dotted_manager_title,
        COALESCE(sk.skills,  '[]'::json)          AS skills,
        COALESCE(ct.cert_count, 0)                AS cert_count,
        COALESCE(ct.certs,   '[]'::json)          AS certifications
    FROM employees e
    LEFT JOIN employee_org_assignments oa  ON oa.employee_id = e.id AND oa.is_current
    LEFT JOIN locations       l  ON l.id  = oa.location_id
    LEFT JOIN business_units  bu ON bu.id = oa.business_unit_id
    LEFT JOIN functional_units fu ON fu.id = oa.functional_unit_id
    LEFT JOIN cost_centers    cc ON cc.id  = oa.cost_center_id
    LEFT JOIN LATERAL (
        SELECT manager_id FROM manager_relationships
        WHERE employee_id = e.id AND relationship_type = 'SOLID_LINE' AND is_current LIMIT 1
    ) sm ON TRUE
    LEFT JOIN employees sm_e ON sm_e.id = sm.manager_id
    LEFT JOIN LATERAL (
        SELECT manager_id FROM manager_relationships
        WHERE employee_id = e.id AND relationship_type = 'DOTTED_LINE' AND is_current LIMIT 1
    ) dm ON TRUE
    LEFT JOIN employees dm_e ON dm_e.id = dm.manager_id
    LEFT JOIN LATERAL (
        SELECT JSON_AGG(JSON_BUILD_OBJECT(
            'skill',      s.name,
            'category',   sc.name,
            'self_level', pl_s.level_name,
            'self_order', pl_s.level_order,
            'val_level',  COALESCE(pl_v.level_name, ''),
            'val_order',  COALESCE(pl_v.level_order, 0),
            'is_primary', es.is_primary_skill,
            'status',     es.validation_status
        ) ORDER BY es.is_primary_skill DESC, pl_s.level_order DESC) AS skills
        FROM employee_skills es
        JOIN skills s             ON s.id  = es.skill_id
        JOIN skill_categories sc  ON sc.id = s.skill_category_id
        JOIN proficiency_levels pl_s ON pl_s.id = es.self_rating_level_id
        LEFT JOIN proficiency_levels pl_v ON pl_v.id = es.manager_validated_level_id
        WHERE es.employee_id = e.id
    ) sk ON TRUE
    LEFT JOIN LATERAL (
        SELECT COUNT(*)::int AS cert_count,
               JSON_AGG(JSON_BUILD_OBJECT(
                   'name',     c.name,
                   'provider', c.provider,
                   'status',   ec.verification_status,
                   'issued',   ec.issued_date,
                   'expiry',   ec.expiry_date
               )) AS certs
        FROM employee_certifications ec
        JOIN certifications c ON c.id = ec.certification_id
        WHERE ec.employee_id = e.id
    ) ct ON TRUE
"""

def fetch_employees(emp_ids=None):
    if emp_ids is None:
        sql = _EMP_SELECT + " WHERE e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name"
        rows = query(sql)
    else:
        if not emp_ids:
            return []
        sql = _EMP_SELECT + " WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name"
        rows = query(sql, (list(emp_ids),))
    return [to_dict(r) for r in rows]

def direct_report_ids(manager_emp_id, line='SOLID_LINE'):
    rows = query(
        "SELECT employee_id::text FROM manager_relationships "
        "WHERE manager_id = %s::uuid AND relationship_type = %s AND is_current",
        (manager_emp_id, line)
    )
    return [r['employee_id'] for r in rows]

def is_direct_report(manager_emp_id, employee_id):
    row = query(
        "SELECT 1 FROM manager_relationships "
        "WHERE manager_id = %s::uuid AND employee_id = %s::uuid AND relationship_type = 'SOLID_LINE' AND is_current",
        (manager_emp_id, employee_id), one=True
    )
    return row is not None

# ─── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        row = query("""
            SELECT u.id::text, u.employee_id::text, u.email,
                   e.first_name, e.last_name, e.job_title,
                   ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
            FROM users u
            JOIN employees e ON e.id = u.employee_id
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            WHERE LOWER(u.email) = %s AND u.is_active
            GROUP BY u.id, u.employee_id, u.email, e.first_name, e.last_name, e.job_title
        """, (email,), one=True)
        if row:
            session.permanent = True
            session['user_id']     = row['id']
            session['employee_id'] = row['employee_id']
            session['user_name']   = f"{row['first_name']} {row['last_name']}"
            session['user_email']  = row['email']
            session['user_title']  = row['job_title'] or ''
            session['roles']       = list(row['roles']) if row['roles'] else ['EMPLOYEE']
            execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (row['id'],))
            return redirect(url_for('dashboard'))
        flash('No active account found for that email address.', 'error')

    demo_users = query("""
        SELECT e.first_name || ' ' || e.last_name AS name, u.email, e.job_title,
               ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
        FROM users u
        JOIN employees e ON e.id = u.employee_id
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE e.employee_number IN (
            'EMP-001','EMP-002','EMP-003','EMP-007','EMP-008','EMP-013'
        )
        GROUP BY u.email, e.first_name, e.last_name, e.job_title, e.employee_number
        ORDER BY e.employee_number
    """)
    return render_template('login.html', demo_users=demo_users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    roles = session.get('roles', [])
    stats = {}

    if any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']):
        stats['total'] = query("SELECT COUNT(*) AS c FROM employees WHERE employment_status='ACTIVE'", one=True)['c']
        stats['by_location'] = [to_dict(r) for r in query("""
            SELECT l.name, l.office_code, COUNT(*) AS count
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            JOIN locations l ON l.id = oa.location_id
            WHERE e.employment_status = 'ACTIVE'
            GROUP BY l.id, l.name, l.office_code ORDER BY count DESC
        """)]
        stats['by_bu'] = [to_dict(r) for r in query("""
            SELECT bu.name, bu.code, COUNT(*) AS count
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            JOIN business_units bu ON bu.id = oa.business_unit_id
            WHERE e.employment_status = 'ACTIVE'
            GROUP BY bu.id, bu.name, bu.code ORDER BY count DESC
        """)]
        stats['top_skills'] = [to_dict(r) for r in query("""
            SELECT s.name, sc.name AS category, COUNT(*) AS emp_count,
                   ROUND(AVG(pl.level_order), 1) AS avg_level
            FROM employee_skills es
            JOIN skills s ON s.id = es.skill_id
            JOIN skill_categories sc ON sc.id = s.skill_category_id
            JOIN proficiency_levels pl ON pl.id = es.self_rating_level_id
            GROUP BY s.id, s.name, sc.name ORDER BY emp_count DESC LIMIT 8
        """)]
        stats['pending_validations'] = query(
            "SELECT COUNT(*) AS c FROM employee_skills WHERE validation_status='SELF_ASSESSED'",
            one=True)['c']
        stats['certs_total'] = query(
            "SELECT COUNT(*) AS c FROM employee_certifications", one=True)['c']

    if any(r in roles for r in ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']):
        emp_id = session['employee_id']
        stats['team_size'] = query("""
            SELECT COUNT(*) AS c FROM manager_relationships
            WHERE manager_id = %s AND relationship_type = 'SOLID_LINE' AND is_current
        """, (emp_id,), one=True)['c']
        stats['team_pending'] = query("""
            SELECT COUNT(*) AS c FROM employee_skills es
            JOIN manager_relationships mr ON mr.employee_id = es.employee_id
            WHERE mr.manager_id = %s AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
              AND es.validation_status = 'SELF_ASSESSED'
        """, (emp_id,), one=True)['c']
        stats['team_certs'] = query("""
            SELECT COUNT(*) AS c FROM employee_certifications ec
            JOIN manager_relationships mr ON mr.employee_id = ec.employee_id
            WHERE mr.manager_id = %s AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
        """, (emp_id,), one=True)['c']

    own = query("""
        SELECT e.first_name, e.last_name, e.job_title, e.join_date,
               COALESCE(l.name,'') AS location,
               COALESCE(bu.name,'') AS bu,
               COALESCE(fu.name,'') AS fu,
               COUNT(DISTINCT es.id) AS skill_count,
               COUNT(DISTINCT ec.id) AS cert_count
        FROM employees e
        LEFT JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
        LEFT JOIN locations l ON l.id = oa.location_id
        LEFT JOIN business_units bu ON bu.id = oa.business_unit_id
        LEFT JOIN functional_units fu ON fu.id = oa.functional_unit_id
        LEFT JOIN employee_skills es ON es.employee_id = e.id
        LEFT JOIN employee_certifications ec ON ec.employee_id = e.id
        WHERE e.id = %s
        GROUP BY e.id, l.name, bu.name, fu.name
    """, (session['employee_id'],), one=True)
    own_dict = to_dict(own) if own else {}
    if own_dict.get('join_date'):
        jd = datetime.date.fromisoformat(own_dict['join_date'])
        own_dict['years'] = (datetime.date.today() - jd).days // 365
    stats['own'] = own_dict

    return render_template('dashboard.html', stats=stats)

# ─── Directory ─────────────────────────────────────────────────────────────────

@app.route('/directory')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER')
def directory():
    departments = [to_dict(r) for r in query("SELECT id::text, name, code FROM business_units ORDER BY name")]
    locations   = [to_dict(r) for r in query("SELECT id::text, name, office_code FROM locations ORDER BY name")]
    return render_template('directory.html', departments=departments, locations=locations)

# ─── My Team ───────────────────────────────────────────────────────────────────

@app.route('/my-team')
@require_roles('SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def my_team():
    return render_template('my_team.html')

# ─── Admin ─────────────────────────────────────────────────────────────────────

@app.route('/admin')
@require_roles('SYSTEM_ADMIN')
def admin():
    all_roles = [to_dict(r) for r in query("SELECT id::text, name, description FROM roles ORDER BY name")]
    return render_template('admin.html', all_roles=all_roles)

# ─── Profile ───────────────────────────────────────────────────────────────────

@app.route('/profile')
@app.route('/profile/<emp_id>')
@login_required
def profile(emp_id=None):
    if emp_id is None:
        emp_id = session['employee_id']

    roles = session.get('roles', [])
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

    emp = rows[0]
    team = []
    if 'SOLID_LINE_MANAGER' in roles and emp_id == current:
        ids = direct_report_ids(current)
        if ids:
            team = fetch_employees(emp_ids=ids)

    return render_template('profile.html', emp=emp, team=team)

# ─── API: employees ────────────────────────────────────────────────────────────

@app.route('/api/employees')
@login_required
def api_employees():
    roles = session.get('roles', [])
    if any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER']):
        data = fetch_employees()
    elif any(r in roles for r in ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']):
        ids = direct_report_ids(session['employee_id'])
        data = fetch_employees(emp_ids=ids)
    else:
        data = fetch_employees(emp_ids=[session['employee_id']])
    return jsonify(data)

@app.route('/api/my-team')
@require_roles('SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def api_my_team():
    ids = direct_report_ids(session['employee_id'])
    return jsonify(fetch_employees(emp_ids=ids))

# ─── API: Admin ────────────────────────────────────────────────────────────────

@app.route('/api/admin/users')
@require_roles('SYSTEM_ADMIN')
def api_admin_users():
    rows = query("""
        SELECT u.id::text, u.username, u.email, u.is_active, u.last_login_at,
               e.employee_number, e.first_name, e.last_name, e.job_title,
               e.id::text AS employee_id,
               e.employment_status,
               COALESCE(l.name, '') AS location,
               ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
        FROM users u
        JOIN employees e ON e.id = u.employee_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
        LEFT JOIN locations l ON l.id = oa.location_id
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        GROUP BY u.id, e.id, l.name
        ORDER BY e.first_name, e.last_name
    """)
    return jsonify([to_dict(r) for r in rows])

@app.route('/api/admin/update-roles', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_update_roles():
    data = request.get_json()
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
                SELECT %s, id FROM roles WHERE name = %s
                ON CONFLICT DO NOTHING
            """, (user_id, rname))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/toggle-user', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_toggle_user():
    data    = request.get_json()
    user_id = data.get('user_id')
    execute("UPDATE users SET is_active = NOT is_active WHERE id = %s", (user_id,))
    row = query("SELECT is_active FROM users WHERE id = %s", (user_id,), one=True)
    return jsonify({'is_active': row['is_active']})

@app.route('/api/admin/validate-skill', methods=['POST'])
@require_roles('SYSTEM_ADMIN', 'SOLID_LINE_MANAGER', 'HR_ADMIN')
def api_validate_skill():
    data = request.get_json()
    skill_id    = data.get('skill_id')
    level_name  = data.get('level')
    status      = data.get('status', 'VALIDATED')
    execute("""
        UPDATE employee_skills
        SET validation_status          = %s,
            manager_validated_level_id = (SELECT id FROM proficiency_levels WHERE level_name = %s),
            updated_at                 = NOW()
        WHERE id = %s
    """, (status, level_name, skill_id))
    return jsonify({'ok': True})

@app.route('/api/admin/org/business-units')
@require_roles('SYSTEM_ADMIN')
def api_org_bus():
    rows = query("""
        SELECT bu.id::text, bu.name, bu.code,
               COUNT(DISTINCT oa.employee_id) AS emp_count
        FROM business_units bu
        LEFT JOIN employee_org_assignments oa ON oa.business_unit_id = bu.id AND oa.is_current
        LEFT JOIN employees e ON e.id = oa.employee_id AND e.employment_status = 'ACTIVE'
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
        LEFT JOIN employee_org_assignments oa ON oa.location_id = l.id AND oa.is_current
        LEFT JOIN employees e ON e.id = oa.employee_id AND e.employment_status = 'ACTIVE'
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
        LEFT JOIN business_units bu ON bu.id = fu.business_unit_id
        LEFT JOIN employee_org_assignments oa ON oa.functional_unit_id = fu.id AND oa.is_current
        LEFT JOIN employees e ON e.id = oa.employee_id AND e.employment_status = 'ACTIVE'
        GROUP BY fu.id, fu.name, fu.code, bu.name ORDER BY bu.name, fu.name
    """)
    return jsonify([to_dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
