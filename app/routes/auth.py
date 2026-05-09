import json
from collections import defaultdict

from flask import session, redirect, url_for, request, render_template, flash

from app import app
from app.db import query, execute, to_dict
from app.auth import login_required


def _login_demo_data():
    """Return structured demo data: tech_admin + per-company role buckets."""
    _tech_row = query("""
        SELECT u.email, e.first_name || ' ' || e.last_name AS name, e.job_title
        FROM users u
        JOIN employees e ON e.id = u.employee_id
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        WHERE r.name = 'SYSTEM_ADMIN' AND e.company_id IS NULL AND u.is_active
        LIMIT 1
    """, one=True)
    tech = to_dict(_tech_row) if _tech_row else None

    companies_raw = [to_dict(r) for r in query(
        "SELECT id::text, name, logo_url, theme_color FROM companies WHERE is_active ORDER BY name"
    )]

    all_users = query("""
        SELECT u.email, e.first_name || ' ' || e.last_name AS name, e.job_title,
               e.company_id::text AS company_id, e.employee_number,
               array_agg(DISTINCT r.name ORDER BY r.name) AS roles
        FROM users u
        JOIN employees e ON e.id = u.employee_id AND e.employment_status = 'ACTIVE'
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.is_active AND e.company_id IS NOT NULL
        GROUP BY u.email, e.first_name, e.last_name, e.job_title, e.company_id, e.employee_number
        ORDER BY e.company_id, e.employee_number
    """)

    LIMITS = {'portal_admins': 1, 'hr_admins': 2, 'solid_managers': 2,
              'dotted_managers': 2, 'contributors': 2}
    buckets = defaultdict(lambda: {k: [] for k in LIMITS})

    for u in all_users:
        roles = set(u['roles'] or ['EMPLOYEE'])
        cid   = u['company_id']
        person = {'email': u['email'], 'name': u['name'], 'job_title': u['job_title']}
        if 'PORTAL_ADMIN' in roles:
            key = 'portal_admins'
        elif 'HR_ADMIN' in roles:
            key = 'hr_admins'
        elif 'SOLID_LINE_MANAGER' in roles and 'DOTTED_LINE_MANAGER' not in roles:
            key = 'solid_managers'
        elif 'DOTTED_LINE_MANAGER' in roles:
            key = 'dotted_managers'
        elif roles <= {'EMPLOYEE'}:
            key = 'contributors'
        else:
            continue
        if len(buckets[cid][key]) < LIMITS[key]:
            buckets[cid][key].append(person)

    companies = []
    for co in companies_raw:
        entry = dict(co)
        entry.update(buckets.get(co['id'], {k: [] for k in LIMITS}))
        companies.append(entry)

    return {'tech_admin': tech, 'companies': companies}


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
                   e.company_id::text AS company_id,
                   COALESCE(u.theme_preference, 'light') AS theme_preference,
                   ARRAY_REMOVE(ARRAY_AGG(r.name ORDER BY r.name), NULL) AS roles
            FROM users u
            JOIN employees e ON e.id = u.employee_id
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            WHERE LOWER(u.email) = %s AND u.is_active
            GROUP BY u.id, u.employee_id, u.email, e.first_name, e.last_name, e.job_title,
                     e.company_id, u.theme_preference
        """, (email,), one=True)
        if row:
            session.permanent = True
            session['user_id']     = row['id']
            session['employee_id'] = row['employee_id']
            session['company_id']  = row['company_id'] or ''
            session['user_name']   = f"{row['first_name']} {row['last_name']}"
            session['user_email']  = row['email']
            session['user_title']  = row['job_title'] or ''
            session['roles']       = list(row['roles']) if row['roles'] else ['EMPLOYEE']
            session['theme_pref']  = row['theme_preference'] or 'light'
            brand = query("""
                SELECT c.theme_color, c.header_html, c.footer_html, c.logo_url, c.name AS company_name
                FROM employees e JOIN companies c ON c.id = e.company_id
                WHERE e.id = %s::uuid
            """, (row['employee_id'],), one=True)
            session['branding'] = to_dict(brand) if brand else {}
            execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (row['id'],))
            return redirect(url_for('dashboard'))
        flash('No active account found for that email address.', 'error')

    demo = _login_demo_data()
    return render_template('login.html',
                           tech_admin=demo['tech_admin'],
                           demo_companies=demo['companies'],
                           demo_companies_json=json.dumps(demo['companies']))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
