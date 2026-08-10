"""Skills Intelligence dashboard — access controlled via role_feature_access matrix."""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import login_required, require_feature_access
from app.db import query, execute
from app.services.company_scope import current_company_id
from app.services import skills_intelligence_service as svc

_FEATURE_CODE = 'skills_intelligence'


# ── company-level gate (separate from role permissions) ───────────────────────

# `_si_enabled` and `_check_si_company_access` were DELETED by KAN-188.
#
# They were a hand-rolled tenant switch: a per-feature read of
# `company_features.is_enabled`, bolted on beside the real permission system and
# duplicated almost verbatim in `analytics.py`. Two copies of an idea that
# belongs in exactly one place (CLAUDE.md: access is decided by the two access
# tables, in one resolver), and every OTHER feature simply went without.
#
# `@require_feature_access('skills_intelligence')` now carries the tenant switch
# itself — effective access is `tenant switch AND role grant` — so these routes
# need no company-level check of their own. Do not reintroduce one: a per-feature
# gate beside the resolver is the `enabled_for_hr` mistake wearing a new hat.


def _resolve_si_scope():
    """Returns (company_id, emp_ids, is_scoped) for the current user."""
    from app.services.company_scope import resolve_report_scope
    roles = session.get('roles', [])
    emp_id = session.get('employee_id')
    company_id = request.args.get('company_id') or current_company_id()
    emp_ids = resolve_report_scope(emp_id, roles)
    is_scoped = emp_ids is not None
    return company_id, emp_ids, is_scoped


# ── Page ──────────────────────────────────────────────────────────────────────

@app.route('/admin/skills-intelligence')
@require_feature_access('skills_intelligence')
def admin_skills_intelligence():
    roles = session.get('roles', [])
    company_id = current_company_id()
    is_sa = 'SYSTEM_ADMIN' in roles

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
    company_id, emp_ids, is_scoped = _resolve_si_scope()
    data = svc.get_kpi_summary(company_id, emp_ids=emp_ids)
    return jsonify({**data, '_scoped': is_scoped})


# ── API: category coverage ────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/coverage')
@require_feature_access('skills_intelligence')
def api_si_coverage():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_category_coverage(company_id, emp_ids=emp_ids))


# ── API: top skills ───────────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/top-skills')
@require_feature_access('skills_intelligence')
def api_si_top_skills():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_top_skills(company_id, emp_ids=emp_ids))


# ── API: benchmark gaps ───────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/gaps')
@require_feature_access('skills_intelligence')
def api_si_gaps():
    company_id, emp_ids, _ = _resolve_si_scope()
    year = int(request.args.get('year', 2025))
    return jsonify(svc.get_benchmark_gaps(company_id, year, emp_ids=emp_ids))


# ── API: proficiency heatmap ──────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/heatmap')
@require_feature_access('skills_intelligence')
def api_si_heatmap():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_proficiency_heatmap(company_id, emp_ids=emp_ids))


# ── API: trend alignment ──────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/trends')
@require_feature_access('skills_intelligence')
def api_si_trends():
    company_id, emp_ids, _ = _resolve_si_scope()
    year = int(request.args.get('year', 2025))
    return jsonify(svc.get_trend_alignment(company_id, year, emp_ids=emp_ids))


# ── API: job title coverage ───────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/job-coverage')
@require_feature_access('skills_intelligence')
def api_si_job_coverage():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_job_title_coverage(company_id, emp_ids=emp_ids))


# ── API: validation funnel ────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/validation')
@require_feature_access('skills_intelligence')
def api_si_validation():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_validation_funnel(company_id, emp_ids=emp_ids))


# ── API: skill growth ─────────────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/growth')
@require_feature_access('skills_intelligence')
def api_si_growth():
    company_id, emp_ids, _ = _resolve_si_scope()
    return jsonify(svc.get_skill_growth(company_id, emp_ids=emp_ids))


# ── API: toggle enabled_for_hr ────────────────────────────────────────────────

@app.route('/api/admin/skills-intelligence/toggle-hr', methods=['POST'])
@require_feature_access('skills_intelligence', 'w')
def api_si_toggle_hr():
    """PORTAL_ADMIN can enable/disable Skills Intelligence for HR Admins in their company.

    ⚠ **TD-17 — `enabled_for_hr` HAS NO CONSUMER.** Nothing reads this column: the
    check that once did was the sub-flag removed for blocking HR_ADMIN even after
    they had been granted access (`CLAUDE.md`, "past mistakes to never repeat").
    KAN-188 deliberately does NOT give it one — a per-feature, per-role side
    channel beside the two access tables is the exact mistake that removal
    corrected, and reviving it would make this the third tenant switch.

    **Removal path:** drop the toggle from `admin/skills_intelligence.html`, delete
    this route, then drop the column. Left in place here only so that removing it
    is a decision somebody takes on purpose rather than a side effect of this
    story. Until then it is a write-only field, and that is the honest state.

    The company-level check that used to sit here is gone — the decorator's
    `skills_intelligence:w` now carries the tenant switch itself.
    """
    company_id = current_company_id()
    if not company_id:
        return jsonify({'error': 'No company context'}), 400

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
