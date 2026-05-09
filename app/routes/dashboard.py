import datetime
import json

from flask import session, render_template, jsonify

from app import app
from app.db import query, to_dict
from app.auth import login_required, require_roles


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


def _dash_company_scope():
    """Return the company_id filter active for the current user session."""
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        return session.get('admin_company_id') or None
    if 'PORTAL_ADMIN' in roles:
        return session.get('company_id') or None
    return None


def compute_dashboard_stats(roles, employee_id, company_id=None):
    stats = {}
    co  = "AND e.company_id = %s::uuid" if company_id else ""
    p   = (company_id,) if company_id else ()

    if any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']):
        stats['total'] = query(
            f"SELECT COUNT(*) AS c FROM employees e WHERE e.employment_status='ACTIVE' {co}",
            p, one=True)['c']

        stats['by_location'] = [to_dict(r) for r in query(f"""
            SELECT l.name, l.office_code, COUNT(*) AS count
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            JOIN locations l ON l.id = oa.location_id
            WHERE e.employment_status = 'ACTIVE' {co}
            GROUP BY l.id, l.name, l.office_code ORDER BY count DESC
        """, p)]

        stats['by_bu'] = [to_dict(r) for r in query(f"""
            SELECT bu.name, bu.code, COUNT(*) AS count
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            JOIN business_units bu ON bu.id = oa.business_unit_id
            WHERE e.employment_status = 'ACTIVE' {co}
            GROUP BY bu.id, bu.name, bu.code ORDER BY count DESC
        """, p)]

        stats['top_skills'] = [to_dict(r) for r in query(f"""
            SELECT s.name, sc.name AS category, COUNT(*) AS emp_count,
                   ROUND(AVG(pl.level_order), 1) AS avg_level
            FROM employee_skills es
            JOIN employees e ON e.id = es.employee_id AND e.employment_status = 'ACTIVE'
            JOIN skills s ON s.id = es.skill_id
            JOIN skill_categories sc ON sc.id = s.skill_category_id
            JOIN proficiency_levels pl ON pl.id = es.self_rating_level_id
            WHERE TRUE {co}
            GROUP BY s.id, s.name, sc.name ORDER BY emp_count DESC LIMIT 8
        """, p)]

        stats['pending_validations'] = query(f"""
            SELECT COUNT(*) AS c FROM employee_skills es
            JOIN employees e ON e.id = es.employee_id
            WHERE es.validation_status = 'SELF_ASSESSED' {co}
        """, p, one=True)['c']

        stats['certs_total'] = query(f"""
            SELECT COUNT(*) AS c FROM employee_certifications ec
            JOIN employees e ON e.id = ec.employee_id
            WHERE TRUE {co}
        """, p, one=True)['c']

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
        rows     = query("SELECT role_name, interval_ms FROM widget_refresh_settings")
        settings = {r['role_name']: r['interval_ms'] for r in rows}
        intervals = [settings[r] for r in roles if r in settings]
        return min(intervals) if intervals else 30000
    except Exception:
        return 30000


@app.route('/dashboard')
@login_required
def dashboard():
    roles      = session.get('roles', [])
    company_id = _dash_company_scope()
    stats      = compute_dashboard_stats(roles, session['employee_id'], company_id=company_id)
    companies  = []
    admin_company_id = ''
    if 'SYSTEM_ADMIN' in roles:
        companies        = _companies_with_admins()
        admin_company_id = session.get('admin_company_id') or ''
    return render_template('dashboard.html',
                           stats=stats,
                           refresh_interval=get_refresh_interval(roles),
                           companies=companies,
                           companies_json=json.dumps(companies),
                           admin_company_id=admin_company_id)


@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    roles      = session.get('roles', [])
    company_id = _dash_company_scope()
    return jsonify(compute_dashboard_stats(roles, session['employee_id'], company_id=company_id))


@app.route('/api/admin/refresh-settings', methods=['GET'])
@require_roles('SYSTEM_ADMIN')
def api_get_refresh_settings():
    rows = query("SELECT role_name, interval_ms FROM widget_refresh_settings ORDER BY interval_ms")
    return jsonify([to_dict(r) for r in rows])


@app.route('/api/admin/refresh-settings', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_set_refresh_settings():
    from flask import request
    data        = request.get_json()
    role_name   = data.get('role_name')
    interval_ms = int(data.get('interval_ms', 0))
    if not role_name or interval_ms < 2000:
        from flask import jsonify as _j
        return _j({'error': 'interval_ms must be >= 2000 (2 seconds)'}), 400
    from app.db import execute
    execute("""
        INSERT INTO widget_refresh_settings (role_name, interval_ms, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (role_name) DO UPDATE
          SET interval_ms = EXCLUDED.interval_ms, updated_at = NOW()
    """, (role_name, interval_ms))
    return jsonify({'ok': True, 'role_name': role_name, 'interval_ms': interval_ms})
