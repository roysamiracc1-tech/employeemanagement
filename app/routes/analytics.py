"""Analytics dashboard — page + API endpoints."""
import csv
import datetime
import io

from flask import session, request, jsonify, render_template, Response

from app import app
from app.auth import login_required, require_roles, require_feature_access
from app.db import query, execute
from app.services.company_scope import current_company_id
from app.services import analytics_service as svc

_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')
_FEATURE_CODE = 'reports'


# ── feature gate ──────────────────────────────────────────────────────────────

def _analytics_enabled(company_id: str) -> bool:
    """Return True if the Analytics feature is enabled for company_id."""
    if not company_id:
        return False
    row = query("""
        SELECT cf.is_enabled
        FROM company_features cf
        JOIN portal_features pf ON pf.id = cf.feature_id
        WHERE cf.company_id = %s::uuid AND pf.code = %s
    """, (company_id, _FEATURE_CODE), one=True)
    return bool(row and row['is_enabled'])


def _check_analytics_access(company_id: str):
    """For PORTAL_ADMIN / HR_ADMIN: block if feature not enabled.
    SYSTEM_ADMIN always has access (they manage the toggle).
    Returns a Response to return early, or None if access is allowed.
    """
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        return None   # super admin always allowed
    if not _analytics_enabled(company_id):
        return jsonify({
            'error': 'Analytics is not enabled for your company. '
                     'Contact your Super Admin to activate this feature.'
        }), 403
    return None

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


# ── feature toggle (SYSTEM_ADMIN only) ───────────────────────────────────────

@app.route('/api/admin/company-features/<company_id>/toggle', methods=['POST'])
@require_roles('SYSTEM_ADMIN')
def api_toggle_company_feature(company_id):
    """Enable or disable a portal feature for a specific company.

    Also accepts optional enabled_for_hr to update the HR sub-toggle
    for features that support it (e.g. skills_intelligence).
    """
    data         = request.get_json() or {}
    feature_code = data.get('feature_code', _FEATURE_CODE)
    enabled      = bool(data.get('enabled', False))
    enabled_for_hr = data.get('enabled_for_hr')  # None means "don't touch"

    feature = query(
        "SELECT id FROM portal_features WHERE code = %s",
        (feature_code,), one=True,
    )
    if not feature:
        return jsonify({'error': 'Unknown feature code'}), 400

    execute("""
        INSERT INTO company_features (company_id, feature_id, is_enabled, enabled_at, enabled_by)
        VALUES (%s::uuid, %s::uuid, %s, CASE WHEN %s THEN NOW() ELSE NULL END, %s::uuid)
        ON CONFLICT (company_id, feature_id) DO UPDATE
          SET is_enabled = EXCLUDED.is_enabled,
              enabled_at = EXCLUDED.enabled_at,
              enabled_by = EXCLUDED.enabled_by
    """, (company_id, feature['id'], enabled, enabled, session['user_id']))

    if enabled_for_hr is not None:
        execute("""
            UPDATE company_features SET enabled_for_hr = %s
            WHERE company_id = %s::uuid AND feature_id = %s::uuid
        """, (bool(enabled_for_hr), company_id, feature['id']))

    return jsonify({'ok': True, 'company_id': company_id,
                    'feature_code': feature_code, 'enabled': enabled})


@app.route('/api/admin/company-features/<company_id>')
@require_roles('SYSTEM_ADMIN')
def api_get_company_features(company_id):
    """Return all feature flags for a company."""
    rows = query("""
        SELECT pf.code, pf.label, cf.is_enabled,
               cf.enabled_at, u.email AS enabled_by_email,
               COALESCE(cf.enabled_for_hr, FALSE) AS enabled_for_hr
        FROM portal_features pf
        LEFT JOIN company_features cf
               ON cf.feature_id = pf.id AND cf.company_id = %s::uuid
        LEFT JOIN users u ON u.id = cf.enabled_by
        ORDER BY pf.sort_order
    """, (company_id,))
    result = []
    for r in rows:
        d = dict(r)
        if d.get('enabled_at'):
            d['enabled_at'] = str(d['enabled_at'])[:10]
        result.append(d)
    return jsonify(result)


# ── page ──────────────────────────────────────────────────────────────────────

@app.route('/admin/analytics')
@require_feature_access(_FEATURE_CODE)
def admin_analytics():
    company_id = _resolve_company()
    is_sa = 'SYSTEM_ADMIN' in session.get('roles', [])
    companies = []
    if is_sa:
        rows = query("SELECT id::text, name FROM companies ORDER BY name")
        # Attach analytics-enabled flag to each company for the SA dropdown
        enabled_ids = {
            r['company_id'] for r in query("""
                SELECT cf.company_id::text
                FROM company_features cf
                JOIN portal_features pf ON pf.id = cf.feature_id
                WHERE pf.code = %s AND cf.is_enabled
            """, (_FEATURE_CODE,))
        }
        companies = [{'id': r['id'], 'name': r['name'],
                      'analytics_enabled': r['id'] in enabled_ids}
                     for r in rows]
    # For non-SA: block if feature not enabled
    if not is_sa and not _analytics_enabled(company_id):
        return render_template('admin/analytics_locked.html')
    return render_template('admin/analytics.html', companies=companies,
                           is_sa=is_sa)


# ── API — overview ────────────────────────────────────────────────────────────

@app.route('/api/analytics/overview')
@require_feature_access(_FEATURE_CODE)
def api_analytics_overview():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked
    start, end = _parse_range()
    return jsonify(svc.get_overview(company_id, start, end))


# ── API — vacation ────────────────────────────────────────────────────────────

@app.route('/api/analytics/vacation')
@require_feature_access(_FEATURE_CODE)
def api_analytics_vacation():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked
    start, end = _parse_range()
    group_by   = request.args.get('group_by', 'company')
    return jsonify(svc.get_vacation_analytics(company_id, start, end, group_by))


# ── API — skills ──────────────────────────────────────────────────────────────

@app.route('/api/analytics/skills')
@require_feature_access(_FEATURE_CODE)
def api_analytics_skills():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked
    start, end = _parse_range()
    return jsonify(svc.get_skills_analytics(company_id, start, end))


# ── API — org ─────────────────────────────────────────────────────────────────

@app.route('/api/analytics/org')
@require_feature_access(_FEATURE_CODE)
def api_analytics_org():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked
    start, end = _parse_range()
    return jsonify(svc.get_org_analytics(company_id, start, end))


# ── API — search ──────────────────────────────────────────────────────────────

@app.route('/api/analytics/search')
@require_feature_access(_FEATURE_CODE)
def api_analytics_search():
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked
    start, end = _parse_range()
    return jsonify(svc.get_search_analytics(company_id, start, end))


# ── API — CSV export ──────────────────────────────────────────────────────────

@app.route('/api/analytics/export/csv')
@require_feature_access(_FEATURE_CODE)
def api_analytics_export_csv():
    """Export one analytics section as a downloadable CSV."""
    company_id = _resolve_company()
    if not company_id:
        return jsonify({'error': 'Select a company'}), 400
    blocked = _check_analytics_access(company_id)
    if blocked:
        return blocked

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
