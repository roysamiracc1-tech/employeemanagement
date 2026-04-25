from flask import session, redirect, url_for, request, render_template, flash

from app import app
from app.db import query, execute, to_dict
from app.auth import login_required


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
        WHERE e.employee_number IN ('EMP-001','EMP-002','EMP-003','EMP-007','EMP-008','EMP-013')
        GROUP BY u.email, e.first_name, e.last_name, e.job_title, e.employee_number
        ORDER BY e.employee_number
    """)
    return render_template('login.html', demo_users=demo_users)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
