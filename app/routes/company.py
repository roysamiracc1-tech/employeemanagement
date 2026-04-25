from flask import session, redirect, url_for, request, render_template, flash, jsonify

from app import app
from app.db import query, execute, insert_returning, to_dict
from app.auth import login_required, require_roles
from app.helpers import company_stats, save_logo


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

    co = query(
        "SELECT id::text,name,industry,website,logo_url,hq_address,founded_year,"
        "description,is_active,created_at,theme_color,header_html,footer_html "
        "FROM companies WHERE id=%s::uuid",
        (company_id,), one=True,
    )
    if not co:
        flash('Company not found.', 'error')
        return redirect(url_for('dashboard'))

    stats = company_stats(company_id)
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

    return render_template('company/view.html',
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
    return render_template('admin/companies.html', companies=companies)


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

        uploaded = save_logo(request.files.get('logo_file'))
        logo_url = uploaded or request.form.get('logo_url', '').strip() or None

        if not name:
            flash('Company name is required.', 'error')
            return redirect(url_for('admin_company_new'))

        insert_returning("""
            INSERT INTO companies
              (name,industry,website,hq_address,founded_year,description,
               logo_url,theme_color,header_html,footer_html)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id::text
        """, (name, industry, website, hq_address,
              int(founded_year) if founded_year else None,
              description, logo_url, theme_color, header_html, footer_html))

        flash(f'Company "{name}" registered successfully.', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin/company_form.html', co=None, action='new')


@app.route('/admin/companies/<company_id>/edit', methods=['GET', 'POST'])
@require_roles('SYSTEM_ADMIN')
def admin_company_edit(company_id):
    co = query(
        "SELECT id::text,name,industry,website,logo_url,hq_address,founded_year,"
        "description,is_active,theme_color,header_html,footer_html "
        "FROM companies WHERE id=%s::uuid",
        (company_id,), one=True,
    )
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

        old_logo  = to_dict(co).get('logo_url')
        uploaded  = save_logo(request.files.get('logo_file'), old_url=old_logo)
        url_field = request.form.get('logo_url', '').strip() or None
        if request.form.get('logo_clear') == '1':
            import os
            if old_logo and old_logo.startswith('/static/uploads/logos/'):
                from app.helpers import _BASE_DIR
                old_path = os.path.join(_BASE_DIR, old_logo.lstrip('/'))
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

        brand = query("""
            SELECT c.theme_color, c.header_html, c.footer_html, c.logo_url, c.name AS company_name
            FROM employees e JOIN companies c ON c.id = e.company_id
            WHERE e.id = %s::uuid
        """, (session['employee_id'],), one=True)
        if brand:
            session['branding'] = to_dict(brand)

        flash(f'Company "{name}" updated.', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin/company_form.html', co=to_dict(co), action='edit')
