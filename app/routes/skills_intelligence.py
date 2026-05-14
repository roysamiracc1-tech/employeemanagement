"""Skills Intelligence dashboard — access controlled via role_feature_access matrix."""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import login_required, require_feature_access
from app.db import query, execute
from app.services.company_scope import current_company_id
from app.services import skills_intelligence_service as svc

_FEATURE_CODE = 'skills_intelligence'


# ── company-level gate (separate from role permissions) ───────────────────────

def _si_enabled(company_id: str) -> bool:
    """Is Skills Intelligence licensed/enabled for this company?"""
    if not company_id:
        return False
    row = query("""
        SELECT cf.is_enabled
        FROM company_features cf
        JOIN portal_features pf ON pf.id = cf.feature_id
        WHERE cf.company_id = %s::uuid AND pf.code = %s
    """, (company_id, _FEATURE_CODE), one=True)
    return bool(row and row['is_enabled'])


def _check_si_company_access(company_id: str):
    """Check company-level enablement only. Role access is handled by @require_feature_access."""
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        return True, None
    if not _si_enabled(company_id):
        return False, (jsonify({'error': 'Skills Intelligence not enabled for this company'}), 403)
    return True, None


# ── Page ──────────────────────────────────────────────────────────────────────

@app.route('/admin/skills-intelligence')
@require_feature_access('skills_intelligence')
def admin_skills_intelligence():
    roles = session.get('roles', [])
    company_id = current_company_id()
    is_sa = 'SYSTEM_ADMIN' in roles

    if not is_sa:
        if not _si_enabled(company_id):
            return render_template('admin/skills_intelligence_locked.html')

    companies = []
    if is_sa:
        companies = [dict(r) for r in query("SELECT id::text, name FROM companies ORDER BY name")]

    return render_template('admin/skills_intelligence.html',
                           companies=companies,
                           is_sa=is_sa,
                           company_id=company_id or '')


# ── API: KPI summary ──────────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/kpi')
@require_feature_access('skills_intelligence')
def api_si_kpi():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_kpi_summary(company_id))


# ── API: category coverage ────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/coverage')
@require_feature_access('skills_intelligence')
def api_si_coverage():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_category_coverage(company_id))


# ── API: top skills ───────────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/top-skills')
@require_feature_access('skills_intelligence')
def api_si_top_skills():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_top_skills(company_id))


# ── API: benchmark gaps ───────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/gaps')
@require_feature_access('skills_intelligence')
def api_si_gaps():
    company_id = request.args.get('company_id') or current_company_id()
    year = int(request.args.get('year', 2025))
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_benchmark_gaps(company_id, year))


# ── API: proficiency heatmap ──────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/heatmap')
@require_feature_access('skills_intelligence')
def api_si_heatmap():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_proficiency_heatmap(company_id))


# ── API: trend alignment ──────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/trends')
@require_feature_access('skills_intelligence')
def api_si_trends():
    company_id = request.args.get('company_id') or current_company_id()
    year = int(request.args.get('year', 2025))
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_trend_alignment(company_id, year))


# ── API: job title coverage ───────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/job-coverage')
@require_feature_access('skills_intelligence')
def api_si_job_coverage():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_job_title_coverage(company_id))


# ── API: validation funnel ────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/validation')
@require_feature_access('skills_intelligence')
def api_si_validation():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_validation_funnel(company_id))


# ── API: skill growth ─────────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/growth')
@require_feature_access('skills_intelligence')
def api_si_growth():
    company_id = request.args.get('company_id') or current_company_id()
    ok, err = _check_si_company_access(company_id)
    if not ok:
        return err
    return jsonify(svc.get_skill_growth(company_id))


# ── API: toggle enabled_for_hr ────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/toggle-hr', methods=['POST'])
@require_feature_access('skills_intelligence', 'w')
def api_si_toggle_hr():
    """PORTAL_ADMIN can enable/disable Skills Intelligence for HR Admins in their company."""
    company_id = current_company_id()
    if not company_id:
        return jsonify({'error': 'No company context'}), 400
    if not _si_enabled(company_id):
        return jsonify({'error': 'Feature not enabled for this company'}), 403

    data = request.get_json(silent=True) or {}
    enabled = bool(data.get('enabled', False))

    feat_id = (query(
        "SELECT id FROM portal_features WHERE code=%s", (_FEATURE_CODE,), one=True) or {}).get('id')
    if not feat_id:
        return jsonify({'error': 'Feature not found'}), 500

    execute("""
        UPDATE company_features
        SET enabled_for_hr = %s
        WHERE company_id = %s::uuid AND feature_id = %s::uuid
    """, (enabled, company_id, feat_id))

    return jsonify({'company_id': company_id, 'enabled_for_hr': enabled})
