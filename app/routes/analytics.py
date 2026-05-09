"""Analytics dashboard — page + API endpoints."""
import csv
import datetime
import io

from flask import session, request, jsonify, render_template, Response

from app import app
from app.auth import login_required, require_roles
from app.db import query
from app.services.company_scope import current_company_id
from app.services import analytics_service as svc

_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')

# ── date parsing helpers ──────────────────────────────────────────────────────

def _parse_range():
    """Return (start, end) as datetime.date from ?start/end or ?range preset."""
    today = datetime.date.today()
    preset = request.args.get('range', '30d')
    start_arg = request.args.get('start')
    end_arg   = request.args.get('end')

    if start_arg and end_arg:
        try:
            return (datetime.date.fromisoformat(start_arg),
                    datetime.date.fromisoformat(end_arg))
        except ValueError:
            pass

    days = {'30d': 30, '90d': 90, '365d': 365}.get(preset, 30)
    return today - datetime.timedelta(days=days), today


def _resolve_company():
    """Return the company_id to report on.

    SYSTEM_ADMIN: honours ?company_id param (dropdown selection).
    PORTAL_ADMIN / HR_ADMIN: always own company.
    """
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        cid = request.args.get('company_id') or current_company_id()
        return cid
    return current_company_id() or session.get('company_id')


# ── page ──────────────────────────────────────────────────────────────────────

@app.route('/admin/analytics')
@require_roles(*_ROLES)
def admin_analytics():
    companies = []
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        companies = [dict(r) for r in query(
            "SELECT id::text, name FROM companies ORDER BY name")]
    return render_template('admin/analytics.html', companies=companies)


# ── API — overview ────────────────────────────────────────────────────────────

@app.route('/api/analytics/overview')
@require_roles(*_ROLES)
def api_analytics_overview():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    start, end = _parse_range()
    return jsonify(svc.get_overview(company_id, start, end))


# ── API — vacation ────────────────────────────────────────────────────────────

@app.route('/api/analytics/vacation')
@require_roles(*_ROLES)
def api_analytics_vacation():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    start, end = _parse_range()
    group_by   = request.args.get('group_by', 'company')
    return jsonify(svc.get_vacation_analytics(company_id, start, end, group_by))


# ── API — skills ──────────────────────────────────────────────────────────────

@app.route('/api/analytics/skills')
@require_roles(*_ROLES)
def api_analytics_skills():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    start, end = _parse_range()
    return jsonify(svc.get_skills_analytics(company_id, start, end))


# ── API — org ─────────────────────────────────────────────────────────────────

@app.route('/api/analytics/org')
@require_roles(*_ROLES)
def api_analytics_org():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    start, end = _parse_range()
    return jsonify(svc.get_org_analytics(company_id, start, end))


# ── API — search ──────────────────────────────────────────────────────────────

@app.route('/api/analytics/search')
@require_roles(*_ROLES)
def api_analytics_search():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    start, end = _parse_range()
    return jsonify(svc.get_search_analytics(company_id, start, end))


# ── API — CSV export ──────────────────────────────────────────────────────────

@app.route('/api/analytics/export/csv')
@require_roles(*_ROLES)
def api_analytics_export_csv():
    """Export one analytics section as a downloadable CSV."""
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400

    section = request.args.get('section', 'vacation')
    start, end = _parse_range()

    rows: list = []
    filename = f'analytics_{section}_{start}_{end}.csv'

    if section == 'overview':
        data = svc.get_overview(company_id, start, end)
        rows = data.get('feature_adoption', [])
    elif section == 'vacation':
        data = svc.get_vacation_analytics(
            company_id, start, end, request.args.get('group_by', 'company'))
        rows = data.get('drilldown', [])
    elif section == 'skills':
        data = svc.get_skills_analytics(company_id, start, end)
        rows = data.get('emp_completeness', [])
    elif section == 'org':
        data = svc.get_org_analytics(company_id, start, end)
        rows = data.get('span_table', [])
    elif section == 'search':
        data = svc.get_search_analytics(company_id, start, end)
        rows = data.get('top_terms', [])

    if not rows:
        return Response('No data', mimetype='text/plain')

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
