import os
import uuid
import decimal
import datetime
from functools import wraps

import psycopg2
import psycopg2.extras
from flask import (Flask, g, session, redirect, url_for, request,
                   render_template, jsonify, flash)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hr-portal-dev-secret-2024')
app.permanent_session_lifetime = datetime.timedelta(hours=8)

_LOGO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'logos')
_ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

def _save_logo(file_storage, old_url=None):
    """Save an uploaded logo, delete old uploaded file if present. Returns public URL or None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in _ALLOWED_IMG:
        return None
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(_LOGO_DIR, exist_ok=True)
    file_storage.save(os.path.join(_LOGO_DIR, filename))
    # Delete the previous uploaded file if it was a local upload
    if old_url and old_url.startswith('/static/uploads/logos/'):
        old_path = os.path.join(os.path.dirname(__file__), old_url.lstrip('/'))
        if os.path.isfile(old_path):
            os.remove(old_path)
    return f"/static/uploads/logos/{filename}"

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

def insert_returning(sql, params=()):
    db = get_db()
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    db.commit()
    return dict(row) if row else None

def serialize(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
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
    branding = session.get('branding') or {}
    theme_pref = session.get('theme_pref', 'light')
    return dict(has_role=has_role, session=session, request=request,
                now=datetime.datetime.now, branding=branding, theme_pref=theme_pref)

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
        COALESCE(e.gender, '')                    AS gender,
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
            'skill_id',      es.skill_id::text,
            'skill',         s.name,
            'category',      sc.name,
            'self_level',    pl_s.level_name,
            'self_level_id', es.self_rating_level_id::text,
            'self_order',    pl_s.level_order,
            'val_level',     COALESCE(pl_v.level_name, ''),
            'val_order',     COALESCE(pl_v.level_order, 0),
            'is_primary',    es.is_primary_skill,
            'status',        es.validation_status
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
                   'ec_id',    ec.id::text,
                   'cert_id',  ec.certification_id::text,
                   'name',     c.name,
                   'provider', c.provider,
                   'status',   ec.verification_status,
                   'issued',   ec.issued_date,
                   'expiry',   ec.expiry_date,
                   'url',      COALESCE(ec.certificate_url, '')
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
                   COALESCE(u.theme_preference, 'light') AS theme_preference,
                   ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
            FROM users u
            JOIN employees e ON e.id = u.employee_id
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            WHERE LOWER(u.email) = %s AND u.is_active
            GROUP BY u.id, u.employee_id, u.email, e.first_name, e.last_name, e.job_title, u.theme_preference
        """, (email,), one=True)
        if row:
            session.permanent = True
            session['user_id']     = row['id']
            session['employee_id'] = row['employee_id']
            session['user_name']   = f"{row['first_name']} {row['last_name']}"
            session['user_email']  = row['email']
            session['user_title']  = row['job_title'] or ''
            session['roles']       = list(row['roles']) if row['roles'] else ['EMPLOYEE']
            session['theme_pref']  = row['theme_preference'] or 'light'
            # Load company branding
            brand = query("""
                SELECT c.theme_color, c.header_html, c.footer_html, c.logo_url, c.name AS company_name
                FROM employees e JOIN companies c ON c.id = e.company_id
                WHERE e.id = %s::uuid
            """, (row['employee_id'],), one=True)
            session['branding'] = to_dict(brand) if brand else {}
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

# ─── Dashboard helpers ─────────────────────────────────────────────────────────

def compute_dashboard_stats(roles, employee_id):
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
        stats['team_size'] = query("""
            SELECT COUNT(*) AS c FROM manager_relationships
            WHERE manager_id = %s::uuid AND relationship_type = 'SOLID_LINE' AND is_current
        """, (employee_id,), one=True)['c']
        stats['team_pending'] = query("""
            SELECT COUNT(*) AS c FROM employee_skills es
            JOIN manager_relationships mr ON mr.employee_id = es.employee_id
            WHERE mr.manager_id = %s::uuid AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
              AND es.validation_status = 'SELF_ASSESSED'
        """, (employee_id,), one=True)['c']
        stats['team_certs'] = query("""
            SELECT COUNT(*) AS c FROM employee_certifications ec
            JOIN manager_relationships mr ON mr.employee_id = ec.employee_id
            WHERE mr.manager_id = %s::uuid AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
        """, (employee_id,), one=True)['c']

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
        WHERE e.id = %s::uuid
        GROUP BY e.id, l.name, bu.name, fu.name
    """, (employee_id,), one=True)
    own_dict = to_dict(own) if own else {}
    if own_dict.get('join_date'):
        jd = datetime.date.fromisoformat(own_dict['join_date'])
        own_dict['years'] = (datetime.date.today() - jd).days // 365
    stats['own'] = own_dict
    return stats


def get_refresh_interval(roles):
    try:
        rows = query("SELECT role_name, interval_ms FROM widget_refresh_settings")
        settings = {r['role_name']: r['interval_ms'] for r in rows}
        intervals = [settings[r] for r in roles if r in settings]
        return min(intervals) if intervals else 30000
    except Exception:
        return 30000


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    roles  = session.get('roles', [])
    stats  = compute_dashboard_stats(roles, session['employee_id'])
    refresh_interval = get_refresh_interval(roles)
    return render_template('dashboard.html', stats=stats, refresh_interval=refresh_interval)

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

    is_own = (emp_id == current)
    all_skills  = [to_dict(r) for r in query("SELECT id::text, name FROM skills ORDER BY name")]
    prof_levels = [to_dict(r) for r in query("SELECT id::text, level_name, level_order FROM proficiency_levels ORDER BY level_order")]
    all_certs   = [to_dict(r) for r in query("SELECT id::text, name, provider FROM certifications ORDER BY name")]

    return render_template('profile.html', emp=emp, team=team,
                           is_own=is_own,
                           all_skills=all_skills,
                           prof_levels=prof_levels,
                           all_certs=all_certs)

# ─── API: profile self-edit ───────────────────────────────────────────────────

@app.route('/api/user/theme', methods=['POST'])
@login_required
def api_user_theme():
    pref = (request.get_json() or {}).get('theme', 'light')
    if pref not in ('light', 'dark'):
        return jsonify({'error': 'Invalid theme'}), 400
    execute("UPDATE users SET theme_preference=%s WHERE id=%s",
            (pref, session['user_id']))
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
    data      = request.get_json()
    emp_id    = session['employee_id']
    skill_id  = data.get('skill_id')
    level_id  = data.get('level_id') or None
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
    emp_id = session['employee_id']
    execute("""
        DELETE FROM employee_skills
        WHERE employee_id = %s::uuid AND skill_id = %s::uuid
    """, (emp_id, skill_id))
    return jsonify({'ok': True})

@app.route('/api/profile/certifications', methods=['POST'])
@login_required
def api_profile_cert_add():
    data    = request.get_json()
    emp_id  = session['employee_id']
    cert_id = data.get('cert_id')
    if not cert_id:
        return jsonify({'error': 'cert_id required'}), 400
    issued  = data.get('issued_date') or None
    expiry  = data.get('expiry_date') or None
    url     = data.get('certificate_url') or None
    row = insert_returning("""
        INSERT INTO employee_certifications
          (employee_id, certification_id, issued_date, expiry_date,
           certificate_url, verification_status)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, 'UNVERIFIED')
        RETURNING id::text
    """, (emp_id, cert_id, issued, expiry, url))
    return jsonify({'ok': True, 'id': row['id']})

@app.route('/api/profile/certifications/<ec_id>', methods=['PUT'])
@login_required
def api_profile_cert_update(ec_id):
    data   = request.get_json()
    emp_id = session['employee_id']
    issued = data.get('issued_date') or None
    expiry = data.get('expiry_date') or None
    url    = data.get('certificate_url') or None
    execute("""
        UPDATE employee_certifications
        SET issued_date = %s, expiry_date = %s, certificate_url = %s
        WHERE id = %s::uuid AND employee_id = %s::uuid
    """, (issued, expiry, url, ec_id, emp_id))
    return jsonify({'ok': True})

@app.route('/api/profile/certifications/<ec_id>', methods=['DELETE'])
@login_required
def api_profile_cert_delete(ec_id):
    emp_id = session['employee_id']
    execute("""
        DELETE FROM employee_certifications
        WHERE id = %s::uuid AND employee_id = %s::uuid
    """, (ec_id, emp_id))
    return jsonify({'ok': True})

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

# ─── Admin: add new employee ───────────────────────────────────────────────────

def _next_employee_number():
    row = query("""
        SELECT COALESCE(MAX(CAST(SPLIT_PART(employee_number,'-',2) AS INTEGER)), 0) AS n
        FROM employees WHERE employee_number ~ '^EMP-[0-9]+$'
    """, one=True)
    return f"EMP-{(row['n'] + 1):03d}"

@app.route('/admin/register-user', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_register_user():
    if request.method == 'POST':
        # ── 1. Collect form data ───────────────────────────────────────────────
        first_name      = request.form.get('first_name', '').strip()
        last_name       = request.form.get('last_name', '').strip()
        emp_email       = request.form.get('emp_email', '').strip().lower()
        phone           = request.form.get('phone', '').strip() or None
        gender          = request.form.get('gender', '').strip() or None
        job_title       = request.form.get('job_title', '').strip() or None
        emp_type        = request.form.get('employment_type', '').strip() or None
        join_date       = request.form.get('join_date', '').strip() or None
        employee_number = request.form.get('employee_number', '').strip()
        location_id     = request.form.get('location_id', '').strip() or None
        bu_id           = request.form.get('business_unit_id', '').strip() or None
        fu_id           = request.form.get('functional_unit_id', '').strip() or None
        cc_id           = request.form.get('cost_center_id', '').strip() or None
        solid_mgr_id    = request.form.get('solid_manager_id', '').strip() or None
        dotted_mgr_id   = request.form.get('dotted_manager_id', '').strip() or None
        username        = request.form.get('username', '').strip()
        roles_list      = request.form.getlist('roles')

        # ── 2. Validate required fields ───────────────────────────────────────
        errors = []
        if not first_name or not last_name:
            errors.append('First and last name are required.')
        if not emp_email:
            errors.append('Work email is required.')
        if not employee_number:
            errors.append('Employee number is required.')
        if not username:
            errors.append('Username is required.')
        if query("SELECT 1 FROM employees WHERE LOWER(email) = %s", (emp_email,), one=True):
            errors.append(f'Email {emp_email} is already in use by another employee.')
        if query("SELECT 1 FROM employees WHERE employee_number = %s", (employee_number,), one=True):
            errors.append(f'Employee number {employee_number} is already taken.')
        if query("SELECT 1 FROM users WHERE username = %s", (username,), one=True):
            errors.append(f'Username "{username}" is already taken.')
        if query("SELECT 1 FROM users WHERE LOWER(email) = %s", (emp_email,), one=True):
            errors.append('A portal account with that email already exists.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return redirect(url_for('admin_register_user'))

        # ── 3. Insert employee record ─────────────────────────────────────────
        emp = insert_returning("""
            INSERT INTO employees
              (employee_number, first_name, last_name, email, phone_number,
               gender, job_title, employment_type, employment_status, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', %s)
            RETURNING id::text
        """, (employee_number, first_name, last_name, emp_email, phone,
              gender, job_title, emp_type, join_date or None))
        emp_id = emp['id']

        # ── 4. Org assignment ─────────────────────────────────────────────────
        if any([location_id, bu_id, fu_id, cc_id]):
            execute("""
                INSERT INTO employee_org_assignments
                  (employee_id, location_id, business_unit_id,
                   functional_unit_id, cost_center_id, is_current)
                VALUES (%s::uuid,
                        %s::uuid, %s::uuid, %s::uuid, %s::uuid,
                        TRUE)
            """, (emp_id, location_id, bu_id, fu_id, cc_id))

        # ── 5. Manager relationships ──────────────────────────────────────────
        if solid_mgr_id:
            execute("""
                INSERT INTO manager_relationships
                  (employee_id, manager_id, relationship_type)
                VALUES (%s::uuid, %s::uuid, 'SOLID_LINE')
                ON CONFLICT DO NOTHING
            """, (emp_id, solid_mgr_id))
        if dotted_mgr_id and dotted_mgr_id != solid_mgr_id:
            execute("""
                INSERT INTO manager_relationships
                  (employee_id, manager_id, relationship_type)
                VALUES (%s::uuid, %s::uuid, 'DOTTED_LINE')
                ON CONFLICT DO NOTHING
            """, (emp_id, dotted_mgr_id))

        # ── 6. Skills ─────────────────────────────────────────────────────────
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
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, 'SELF_ASSESSED')
                ON CONFLICT (employee_id, skill_id) DO NOTHING
            """, (emp_id, sid, level_id or None, is_primary))

        # ── 7. Portal account + roles ─────────────────────────────────────────
        user = insert_returning("""
            INSERT INTO users (employee_id, email, username, is_active)
            VALUES (%s::uuid, %s, %s, TRUE)
            RETURNING id::text
        """, (emp_id, emp_email, username))
        user_id = user['id']

        assigned = set(roles_list) | {'EMPLOYEE'}
        for role_name in assigned:
            execute("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s::uuid, id FROM roles WHERE name = %s
                ON CONFLICT DO NOTHING
            """, (user_id, role_name))

        flash(f'Employee {first_name} {last_name} ({employee_number}) added successfully.', 'success')
        return redirect(url_for('admin'))

    # ── GET: build form context ────────────────────────────────────────────────
    locations  = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]
    bus        = [to_dict(r) for r in query("SELECT id::text, name FROM business_units ORDER BY name")]
    fus        = [to_dict(r) for r in query("SELECT id::text, name, business_unit_id::text FROM functional_units ORDER BY name")]
    cost_centers = [to_dict(r) for r in query("SELECT id::text, name FROM cost_centers ORDER BY name")]
    all_employees = [to_dict(r) for r in query("""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title
        FROM employees e WHERE e.employment_status = 'ACTIVE'
        ORDER BY e.first_name, e.last_name
    """)]
    all_roles = [to_dict(r) for r in query("SELECT id::text, name, description FROM roles ORDER BY name")]
    all_skills = [to_dict(r) for r in query("SELECT id::text, name FROM skills ORDER BY name")]
    prof_levels = [to_dict(r) for r in query("SELECT id::text, level_name, level_order FROM proficiency_levels ORDER BY level_order")]
    next_emp_num = _next_employee_number()
    return render_template('admin_register.html',
                           locations=locations, bus=bus, fus=fus,
                           cost_centers=cost_centers,
                           all_employees=all_employees,
                           all_roles=all_roles,
                           all_skills=all_skills,
                           prof_levels=prof_levels,
                           next_emp_num=next_emp_num)

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    roles = session.get('roles', [])
    stats = compute_dashboard_stats(roles, session['employee_id'])
    return jsonify(stats)

@app.route('/api/admin/refresh-settings', methods=['GET'])
@require_roles('SYSTEM_ADMIN')
def api_get_refresh_settings():
    rows = query("SELECT role_name, interval_ms FROM widget_refresh_settings ORDER BY interval_ms")
    return jsonify([to_dict(r) for r in rows])

@app.route('/api/admin/refresh-settings', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_set_refresh_settings():
    data = request.get_json()
    role_name   = data.get('role_name')
    interval_ms = int(data.get('interval_ms', 0))
    if not role_name or interval_ms < 2000:
        return jsonify({'error': 'interval_ms must be >= 2000 (2 seconds)'}), 400
    execute("""
        INSERT INTO widget_refresh_settings (role_name, interval_ms, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (role_name) DO UPDATE
          SET interval_ms = EXCLUDED.interval_ms, updated_at = NOW()
    """, (role_name, interval_ms))
    return jsonify({'ok': True, 'role_name': role_name, 'interval_ms': interval_ms})

# ─── Org Tree ─────────────────────────────────────────────────────────────────

MGMT_ROLES = ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
              'LOCATION_HEAD', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']

@app.route('/org-tree')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
               'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def org_tree():
    roles    = session.get('roles', [])
    is_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN',
                                        'DEPARTMENT_HEAD', 'LOCATION_HEAD'])
    all_employees = []
    if is_admin:
        all_employees = [to_dict(r) for r in query("""
            SELECT e.id::text, e.first_name, e.last_name, e.job_title
            FROM employees e WHERE e.employment_status='ACTIVE'
            ORDER BY e.first_name, e.last_name
        """)]
    return render_template('org_tree.html',
                           is_admin=is_admin,
                           own_emp_id=session['employee_id'],
                           all_employees=all_employees)

_TREE_CTE = """
    WITH RECURSIVE tree AS (
        SELECT e.id,
               e.first_name, e.last_name, e.job_title,
               e.employment_type,
               COALESCE(l.name,'')  AS location,
               COALESCE(bu.name,'') AS business_unit,
               NULL::uuid           AS manager_id,
               0                    AS depth
        FROM employees e
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l       ON l.id=oa.location_id
        LEFT JOIN business_units bu ON bu.id=oa.business_unit_id
        WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE'

        UNION ALL

        SELECT e.id,
               e.first_name, e.last_name, e.job_title,
               e.employment_type,
               COALESCE(l.name,'')  AS location,
               COALESCE(bu.name,'') AS business_unit,
               mr.manager_id,
               t.depth + 1
        FROM employees e
        JOIN manager_relationships mr
             ON mr.employee_id = e.id
             AND mr.relationship_type = 'SOLID_LINE'
             AND mr.is_current
        JOIN tree t ON t.id = mr.manager_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l       ON l.id=oa.location_id
        LEFT JOIN business_units bu ON bu.id=oa.business_unit_id
        WHERE e.employment_status='ACTIVE' AND t.depth < 10
    )
    SELECT id::text, first_name, last_name, job_title, employment_type,
           location, business_unit, manager_id::text, depth
    FROM tree ORDER BY depth, last_name
"""

def _build_nested(flat):
    nodes = {r['id']: {**r, 'children': []} for r in flat}
    roots = []
    for r in flat:
        if r['manager_id'] is None or r['manager_id'] not in nodes:
            roots.append(nodes[r['id']])
        else:
            nodes[r['manager_id']]['children'].append(nodes[r['id']])
    return roots

@app.route('/api/org-tree')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
               'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def api_org_tree():
    roles    = session.get('roles', [])
    is_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN',
                                        'DEPARTMENT_HEAD', 'LOCATION_HEAD'])
    root_id  = request.args.get('root', '').strip()

    if not is_admin:
        # Managers always see their own subtree
        root_ids = [session['employee_id']]
    elif root_id:
        root_ids = [root_id]
    else:
        # Full org: find employees with no solid-line manager
        top_rows = query("""
            SELECT e.id::text FROM employees e
            WHERE e.employment_status = 'ACTIVE'
              AND NOT EXISTS (
                  SELECT 1 FROM manager_relationships mr
                  WHERE mr.employee_id = e.id
                    AND mr.relationship_type = 'SOLID_LINE'
                    AND mr.is_current
              )
            ORDER BY e.first_name, e.last_name
        """)
        root_ids = [r['id'] for r in top_rows]

    if not root_ids:
        return jsonify([])

    rows = query(_TREE_CTE, (root_ids,))
    flat  = [to_dict(r) for r in rows]
    roots = _build_nested(flat)
    return jsonify(roots if len(roots) != 1 else roots[0])

# ─── Company management ────────────────────────────────────────────────────────

def _company_stats(company_id):
    return query("""
        SELECT
          COUNT(*)::int                                                    AS total,
          COUNT(*) FILTER (WHERE employment_status='ACTIVE')::int         AS active,
          COUNT(*) FILTER (WHERE employment_type='PERMANENT')::int        AS permanent,
          COUNT(*) FILTER (WHERE employment_type='CONTRACTOR')::int       AS contractors,
          COUNT(DISTINCT oa.business_unit_id)::int                        AS bu_count,
          COUNT(DISTINCT oa.location_id)::int                             AS loc_count
        FROM employees e
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        WHERE e.company_id = %s::uuid
    """, (company_id,), one=True)

@app.route('/company')
@app.route('/company/<company_id>')
@login_required
def company_view(company_id=None):
    if company_id is None:
        emp = query("SELECT company_id::text FROM employees WHERE id=%s::uuid",
                    (session['employee_id'],), one=True)
        if not emp or not emp['company_id']:
            flash('No company assigned to your profile.', 'error')
            return redirect(url_for('dashboard'))
        company_id = emp['company_id']

    co = query("SELECT id::text,name,industry,website,logo_url,hq_address,founded_year,description,is_active,created_at,theme_color,header_html,footer_html FROM companies WHERE id=%s::uuid", (company_id,), one=True)
    if not co:
        flash('Company not found.', 'error')
        return redirect(url_for('dashboard'))

    stats = _company_stats(company_id)
    bus   = query("""
        SELECT bu.name, COUNT(DISTINCT e.id)::int AS emp_count
        FROM business_units bu
        JOIN employee_org_assignments oa ON oa.business_unit_id=bu.id AND oa.is_current
        JOIN employees e ON e.id=oa.employee_id AND e.company_id=%s::uuid
        GROUP BY bu.name ORDER BY emp_count DESC
    """, (company_id,))
    locs  = query("""
        SELECT l.name, COUNT(DISTINCT e.id)::int AS emp_count
        FROM locations l
        JOIN employee_org_assignments oa ON oa.location_id=l.id AND oa.is_current
        JOIN employees e ON e.id=oa.employee_id AND e.company_id=%s::uuid
        GROUP BY l.name ORDER BY emp_count DESC
    """, (company_id,))

    return render_template('company.html',
                           co=to_dict(co),
                           stats=to_dict(stats),
                           bus=[to_dict(r) for r in bus],
                           locs=[to_dict(r) for r in locs],
                           can_edit='SYSTEM_ADMIN' in session.get('roles', []))

@app.route('/admin/companies')
@require_roles('SYSTEM_ADMIN')
def admin_companies():
    rows = query("""
        SELECT c.id::text, c.name, c.industry, c.website, c.hq_address,
               c.founded_year, c.is_active, c.created_at,
               COUNT(e.id)::int AS emp_count
        FROM companies c
        LEFT JOIN employees e ON e.company_id=c.id AND e.employment_status='ACTIVE'
        GROUP BY c.id ORDER BY c.name
    """)
    companies = []
    for r in rows:
        d = to_dict(r)
        d['registered_label'] = r['created_at'].strftime('%b %Y') if r['created_at'] else '—'
        companies.append(d)
    return render_template('admin_companies.html', companies=companies)

@app.route('/admin/companies/new', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_company_new():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        industry     = request.form.get('industry', '').strip() or None
        website      = request.form.get('website', '').strip() or None
        hq_address   = request.form.get('hq_address', '').strip() or None
        founded_year = request.form.get('founded_year', '').strip() or None
        description  = request.form.get('description', '').strip() or None
        theme_color  = request.form.get('theme_color', '').strip() or '#2563eb'
        header_html  = request.form.get('header_html', '').strip() or None
        footer_html  = request.form.get('footer_html', '').strip() or None

        # Logo: uploaded file takes priority over URL field
        uploaded = _save_logo(request.files.get('logo_file'))
        logo_url = uploaded or request.form.get('logo_url', '').strip() or None

        if not name:
            flash('Company name is required.', 'error')
            return redirect(url_for('admin_company_new'))

        insert_returning("""
            INSERT INTO companies (name,industry,website,hq_address,founded_year,description,logo_url,theme_color,header_html,footer_html)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id::text
        """, (name, industry, website, hq_address,
              int(founded_year) if founded_year else None,
              description, logo_url, theme_color, header_html, footer_html))

        flash(f'Company "{name}" registered successfully.', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin_company_form.html', co=None, action='new')

@app.route('/admin/companies/<company_id>/edit', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_company_edit(company_id):
    co = query("SELECT id::text,name,industry,website,logo_url,hq_address,founded_year,description,is_active,theme_color,header_html,footer_html FROM companies WHERE id=%s::uuid", (company_id,), one=True)
    if not co:
        flash('Company not found.', 'error')
        return redirect(url_for('admin_companies'))

    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        industry     = request.form.get('industry', '').strip() or None
        website      = request.form.get('website', '').strip() or None
        hq_address   = request.form.get('hq_address', '').strip() or None
        founded_year = request.form.get('founded_year', '').strip() or None
        description  = request.form.get('description', '').strip() or None
        theme_color  = request.form.get('theme_color', '').strip() or '#2563eb'
        header_html  = request.form.get('header_html', '').strip() or None
        footer_html  = request.form.get('footer_html', '').strip() or None
        is_active    = request.form.get('is_active') == '1'

        # Logo: uploaded file > URL field > keep existing
        old_logo  = to_dict(co).get('logo_url')
        uploaded  = _save_logo(request.files.get('logo_file'), old_url=old_logo)
        url_field = request.form.get('logo_url', '').strip() or None
        if request.form.get('logo_clear') == '1':
            # Admin explicitly cleared the logo
            if old_logo and old_logo.startswith('/static/uploads/logos/'):
                old_path = os.path.join(os.path.dirname(__file__), old_logo.lstrip('/'))
                if os.path.isfile(old_path):
                    os.remove(old_path)
            logo_url = None
        else:
            logo_url = uploaded or url_field or old_logo

        if not name:
            flash('Company name is required.', 'error')
            return redirect(url_for('admin_company_edit', company_id=company_id))

        execute("""
            UPDATE companies SET name=%s, industry=%s, website=%s, hq_address=%s,
                founded_year=%s, description=%s, logo_url=%s,
                theme_color=%s, header_html=%s, footer_html=%s,
                is_active=%s, updated_at=NOW()
            WHERE id=%s::uuid
        """, (name, industry, website, hq_address,
              int(founded_year) if founded_year else None,
              description, logo_url, theme_color, header_html, footer_html,
              is_active, company_id))

        # Refresh branding in session if this is the logged-in user's company
        brand = query("""
            SELECT c.theme_color, c.header_html, c.footer_html, c.logo_url, c.name AS company_name
            FROM employees e JOIN companies c ON c.id = e.company_id
            WHERE e.id = %s::uuid
        """, (session['employee_id'],), one=True)
        if brand:
            session['branding'] = to_dict(brand)

        flash(f'Company "{name}" updated.', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin_company_form.html', co=to_dict(co), action='edit')

# ─── Vacation helpers ──────────────────────────────────────────────────────────

def _vacation_types_for_employee(emp_id):
    """Return vacation types the employee is eligible for (location + rules)."""
    emp_info = query("""
        SELECT e.gender, e.join_date, e.company_id::text
        FROM employees e WHERE e.id = %s::uuid
    """, (emp_id,), one=True)
    if not emp_info:
        return []

    # 1. Location-filtered types for this employee's company
    types = [to_dict(r) for r in query("""
        SELECT vt.id::text, vt.name, vt.description, vt.max_days_per_year,
               vt.is_paid, vt.color,
               CASE WHEN COALESCE(vtl_count.cnt,0) = 0
                    THEN 'Company-wide' ELSE 'Location-specific' END AS scope
        FROM vacation_types vt
        LEFT JOIN (
            SELECT vacation_type_id, COUNT(*) AS cnt
            FROM vacation_type_locations GROUP BY vacation_type_id
        ) vtl_count ON vtl_count.vacation_type_id = vt.id
        WHERE vt.is_active AND vt.company_id = %s::uuid
          AND (
            COALESCE(vtl_count.cnt,0) = 0
            OR EXISTS (
                SELECT 1 FROM vacation_type_locations vtl2
                JOIN employee_org_assignments oa
                     ON oa.location_id = vtl2.location_id AND oa.is_current
                WHERE vtl2.vacation_type_id = vt.id AND oa.employee_id = %s::uuid
            )
          )
        ORDER BY vt.name
    """, (emp_info['company_id'], emp_id))]

    if not types:
        return []

    # 2. Fetch all rules for these types
    type_ids = [t['id'] for t in types]
    rules_rows = query("""
        SELECT vacation_type_id::text, rule_type, rule_value
        FROM vacation_type_rules WHERE vacation_type_id = ANY(%s::uuid[])
    """, (type_ids,))

    from collections import defaultdict
    rules_by_type = defaultdict(list)
    for r in rules_rows:
        rules_by_type[r['vacation_type_id']].append(to_dict(r))

    # 3. Compute employee calculated fields once
    today      = datetime.date.today()
    join_date  = emp_info['join_date']
    gender     = (emp_info['gender'] or '').upper()
    tenure_mo  = (today - join_date).days / 30.44  if join_date else 0
    tenure_yr  = (today - join_date).days / 365.25 if join_date else 0

    # 4. Apply rules — all rules for a type must pass (AND logic)
    eligible = []
    for t in types:
        rules = rules_by_type.get(t['id'], [])
        passed = True
        fail_reason = None
        for rule in rules:
            rt, rv = rule['rule_type'], rule['rule_value']
            if rt == 'GENDER_EQ':
                if gender != rv.upper():
                    passed = False
                    fail_reason = f'Requires gender: {rv.title()}'
                    break
            elif rt == 'MIN_TENURE_MONTHS':
                if tenure_mo < float(rv):
                    passed = False
                    fail_reason = f'Requires ≥ {rv} months tenure (you have {tenure_mo:.0f}m)'
                    break
            elif rt == 'MIN_TENURE_YEARS':
                if tenure_yr < float(rv):
                    passed = False
                    fail_reason = f'Requires ≥ {rv} years tenure (you have {tenure_yr:.1f}y)'
                    break
        if passed:
            t['rules'] = rules
            t['rule_labels'] = [_rule_label(r) for r in rules]
            eligible.append(t)
    return eligible

def _rule_label(rule):
    rt, rv = rule['rule_type'], rule['rule_value']
    if rt == 'GENDER_EQ':        return f'Gender: {rv.title()}'
    if rt == 'MIN_TENURE_MONTHS': return f'Min tenure: {rv} months'
    if rt == 'MIN_TENURE_YEARS':  return f'Min tenure: {rv} year{"s" if float(rv)!=1 else ""}'
    return rt

def _employee_solid_manager(emp_id):
    row = query("""
        SELECT manager_id::text FROM manager_relationships
        WHERE employee_id = %s::uuid AND relationship_type='SOLID_LINE' AND is_current
        LIMIT 1
    """, (emp_id,), one=True)
    return row['manager_id'] if row else None

def _used_days(emp_id, vt_id, year):
    row = query("""
        SELECT COALESCE(SUM(working_days),0)::int AS used
        FROM vacation_requests
        WHERE employee_id=%s::uuid AND vacation_type_id=%s::uuid
          AND status IN ('PENDING','APPROVED')
          AND EXTRACT(YEAR FROM start_date) = %s
    """, (emp_id, vt_id, year), one=True)
    return row['used'] if row else 0

@app.route('/api/admin/vacation-rules')
@require_roles('SYSTEM_ADMIN')
def api_admin_vacation_rules():
    ids = [i.strip() for i in request.args.get('ids','').split(',') if i.strip()]
    if not ids:
        return jsonify({})
    rows = query("""
        SELECT vacation_type_id::text, rule_type, rule_value
        FROM vacation_type_rules WHERE vacation_type_id = ANY(%s::uuid[])
        ORDER BY created_at
    """, (ids,))
    result = {i: [] for i in ids}
    for r in rows:
        result[r['vacation_type_id']].append({'rule_type': r['rule_type'], 'rule_value': r['rule_value']})
    return jsonify(result)

# ─── Vacation: employee ────────────────────────────────────────────────────────

@app.route('/vacation')
@login_required
def vacation_page():
    emp_id = session['employee_id']
    mgr_id = _employee_solid_manager(emp_id)
    vt     = _vacation_types_for_employee(emp_id)
    year   = datetime.date.today().year

    # Enrich with used/remaining days
    for t in vt:
        used = _used_days(emp_id, t['id'], year)
        t['used_days'] = used
        t['remaining'] = (t['max_days_per_year'] - used) if t['max_days_per_year'] else None

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

    return render_template('vacation.html',
                           vacation_types=vt,
                           requests=requests,
                           has_manager=bool(mgr_id),
                           year=year)

@app.route('/api/vacation/request', methods=['POST'])
@login_required
def api_vacation_submit():
    emp_id = session['employee_id']
    mgr_id = _employee_solid_manager(emp_id)
    if not mgr_id:
        return jsonify({'error': 'No manager assigned — cannot submit vacation request.'}), 400

    data   = request.get_json()
    vt_id  = data.get('vacation_type_id')
    start  = data.get('start_date')
    end    = data.get('end_date')
    notes  = (data.get('notes') or '').strip() or None

    if not vt_id or not start or not end:
        return jsonify({'error': 'vacation_type_id, start_date and end_date are required.'}), 400

    # Validate type is available to this employee
    allowed = [t['id'] for t in _vacation_types_for_employee(emp_id)]
    if vt_id not in allowed:
        return jsonify({'error': 'This vacation type is not available for your location.'}), 403

    start_d = datetime.date.fromisoformat(start)
    end_d   = datetime.date.fromisoformat(end)
    if end_d < start_d:
        return jsonify({'error': 'End date must be on or after start date.'}), 400

    # Working days = weekdays only
    days = sum(1 for i in range((end_d - start_d).days + 1)
               if (start_d + datetime.timedelta(i)).weekday() < 5)
    days = max(days, 1)

    # Check max_days_per_year
    vt_row = query("SELECT max_days_per_year FROM vacation_types WHERE id=%s::uuid",
                   (vt_id,), one=True)
    if vt_row and vt_row['max_days_per_year']:
        used = _used_days(emp_id, vt_id, start_d.year)
        if used + days > vt_row['max_days_per_year']:
            return jsonify({'error': f'Exceeds annual limit. Used {used}/{vt_row["max_days_per_year"]} days.'}), 400

    row = insert_returning("""
        INSERT INTO vacation_requests
          (employee_id, vacation_type_id, manager_id, start_date, end_date, working_days, notes)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s)
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
    execute("""
        UPDATE vacation_requests SET status='CANCELLED', updated_at=NOW()
        WHERE id=%s::uuid
    """, (req_id,))
    return jsonify({'ok': True})

# ─── Vacation: manager ─────────────────────────────────────────────────────────

@app.route('/vacation/team')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def vacation_team():
    return render_template('vacation_team.html')

@app.route('/api/vacation/team-pending')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
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
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
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
        ORDER BY vr.start_date
        LIMIT 60
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
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def api_vacation_review(req_id):
    data   = request.get_json()
    action = data.get('action')   # 'approve' or 'reject'
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

# ─── Vacation: admin types management ─────────────────────────────────────────

@app.route('/admin/vacation-types')
@require_roles('SYSTEM_ADMIN')
def admin_vacation_types():
    rows = query("""
        SELECT vt.id::text, vt.name, vt.description, vt.max_days_per_year,
               vt.is_paid, vt.color, vt.is_active,
               c.name AS company_name,
               ARRAY_AGG(l.name ORDER BY l.name) FILTER (WHERE l.name IS NOT NULL) AS locations
        FROM vacation_types vt
        JOIN companies c ON c.id = vt.company_id
        LEFT JOIN vacation_type_locations vtl ON vtl.vacation_type_id = vt.id
        LEFT JOIN locations l ON l.id = vtl.location_id
        GROUP BY vt.id, c.name
        ORDER BY c.name, vt.name
    """)
    return render_template('admin_vacation_types.html',
                           types=[to_dict(r) for r in rows])

@app.route('/admin/vacation-types/new', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_vacation_type_new():
    companies = [to_dict(r) for r in query("SELECT id::text, name FROM companies WHERE is_active ORDER BY name")]
    locations = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]

    if request.method == 'POST':
        company_id = request.form.get('company_id')
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
            VALUES (%s::uuid, %s, %s, %s, %s, %s) RETURNING id::text
        """, (company_id, name, desc, int(max_days) if max_days else None, is_paid, color))

        for lid in loc_ids:
            execute("INSERT INTO vacation_type_locations VALUES (%s::uuid, %s::uuid)",
                    (vt['id'], lid))

        rule_types  = request.form.getlist('rule_type')
        rule_values = request.form.getlist('rule_value')
        for rt, rv in zip(rule_types, rule_values):
            if rt and rv:
                execute("INSERT INTO vacation_type_rules (vacation_type_id, rule_type, rule_value) VALUES (%s::uuid,%s,%s)",
                        (vt['id'], rt, rv))

        flash(f'Vacation type "{name}" created.', 'success')
        return redirect(url_for('admin_vacation_types'))

    return render_template('admin_vacation_type_form.html',
                           vt=None, action='new',
                           companies=companies, locations=locations)

@app.route('/admin/vacation-types/<vt_id>/edit', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_vacation_type_edit(vt_id):
    companies = [to_dict(r) for r in query("SELECT id::text, name FROM companies WHERE is_active ORDER BY name")]
    locations = [to_dict(r) for r in query("SELECT id::text, name FROM locations ORDER BY name")]
    vt_row    = query("SELECT id::text,company_id::text,name,description,max_days_per_year,is_paid,color,is_active FROM vacation_types WHERE id=%s::uuid", (vt_id,), one=True)
    if not vt_row:
        flash('Not found.', 'error')
        return redirect(url_for('admin_vacation_types'))

    assigned_locs  = [r['location_id'] for r in query(
        "SELECT location_id::text FROM vacation_type_locations WHERE vacation_type_id=%s::uuid", (vt_id,))]
    existing_rules = [to_dict(r) for r in query(
        "SELECT rule_type, rule_value FROM vacation_type_rules WHERE vacation_type_id=%s::uuid ORDER BY created_at", (vt_id,))]

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        desc     = request.form.get('description', '').strip() or None
        max_days = request.form.get('max_days_per_year', '').strip() or None
        is_paid  = request.form.get('is_paid') == '1'
        color    = request.form.get('color', '#3b82f6').strip()
        is_active= request.form.get('is_active') == '1'
        loc_ids  = request.form.getlist('location_ids')

        execute("""
            UPDATE vacation_types SET name=%s, description=%s, max_days_per_year=%s,
                is_paid=%s, color=%s, is_active=%s WHERE id=%s::uuid
        """, (name, desc, int(max_days) if max_days else None, is_paid, color, is_active, vt_id))

        execute("DELETE FROM vacation_type_locations WHERE vacation_type_id=%s::uuid", (vt_id,))
        for lid in loc_ids:
            execute("INSERT INTO vacation_type_locations VALUES (%s::uuid, %s::uuid)", (vt_id, lid))

        execute("DELETE FROM vacation_type_rules WHERE vacation_type_id=%s::uuid", (vt_id,))
        rule_types  = request.form.getlist('rule_type')
        rule_values = request.form.getlist('rule_value')
        for rt, rv in zip(rule_types, rule_values):
            if rt and rv:
                execute("INSERT INTO vacation_type_rules (vacation_type_id, rule_type, rule_value) VALUES (%s::uuid,%s,%s)",
                        (vt_id, rt, rv))

        flash(f'"{name}" updated.', 'success')
        return redirect(url_for('admin_vacation_types'))

    return render_template('admin_vacation_type_form.html',
                           vt=to_dict(vt_row), action='edit',
                           companies=companies, locations=locations,
                           assigned_locs=assigned_locs,
                           existing_rules=existing_rules)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
