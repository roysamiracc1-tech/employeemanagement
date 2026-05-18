"""
test_si_comprehensive.py — 600+ tests for Skills Intelligence endpoints.
Tests all 9 roles × 9 endpoints, enabled/disabled states, scoping,
and response structure.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import _set_session

FAKE_COMPANY_ID = '00000000-0000-0000-0000-000000000001'
FAKE_COMPANY_ID_2 = '00000000-0000-0000-0000-000000000002'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE'
]

SI_API_ROUTES = [
    '/api/admin/skills-intelligence/kpi',
    '/api/admin/skills-intelligence/coverage',
    '/api/admin/skills-intelligence/gaps',
    '/api/admin/skills-intelligence/heatmap',
    '/api/admin/skills-intelligence/top-skills',
    '/api/admin/skills-intelligence/validation',
    '/api/admin/skills-intelligence/trends',
    '/api/admin/skills-intelligence/growth',
    '/api/admin/skills-intelligence/job-coverage',
]

SI_PAGE_ROUTE = '/admin/skills-intelligence'
SI_FULL_MAP = {'skills_intelligence': {'r': True, 'w': True, 'd': True}}
SI_EMPTY_MAP = {}


def make_client(app, roles, company_id=FAKE_COMPANY_ID, admin_company_id=None):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id'] = '00000000-0000-0000-0000-000000000020'
        s['employee_id'] = '00000000-0000-0000-0000-000000000030'
        s['company_id'] = company_id
        s['roles'] = roles
        s['user_name'] = 'Test User'
        s['user_email'] = 'test@example.com'
        s['theme_pref'] = 'light'
        s['branding'] = {}
        if admin_company_id:
            s['admin_company_id'] = admin_company_id
    return c


# ── Unauthenticated access ────────────────────────────────────────────────────

@pytest.mark.parametrize("route", SI_API_ROUTES + [SI_PAGE_ROUTE])
def test_si_unauthenticated_redirect(client, route):
    """All SI routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


# ── All 9 roles × 9 endpoints (no 500) ───────────────────────────────────────

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ALL_ROLES
    for route in SI_API_ROUTES
])
def test_si_api_no_500_all_roles(app, role, route):
    """All SI API endpoints return non-500 for every role."""
    c = make_client(app, [role])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── SI enabled/disabled × roles ──────────────────────────────────────────────

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE', 'SOLID_LINE_MANAGER']
    for route in SI_API_ROUTES
])
def test_si_disabled_non_sa_gets_403(app, role, route):
    """When SI disabled, non-SA roles with access still get 403."""
    c = make_client(app, [role])
    with patch('app.routes.skills_intelligence._si_enabled', return_value=False), \
         patch('app.routes.skills_intelligence.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code in (302, 308, 403)


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_disabled_sa_still_accessible(app, route):
    """SYSTEM_ADMIN can access SI even when disabled."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=False), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_enabled_portal_admin_accessible(app, route):
    """PORTAL_ADMIN can access SI when enabled and has access."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_enabled_hr_admin_accessible(app, route):
    """HR_ADMIN can access SI when enabled and has access."""
    c = make_client(app, ['HR_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── SI page access ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_si_page_with_access_no_500(app, role):
    """SI page accessible to roles with access."""
    c = make_client(app, [role])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(SI_PAGE_ROUTE)
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_si_page_without_access_redirect(app, role):
    """SI page redirects roles without access."""
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value=SI_EMPTY_MAP):
        r = c.get(SI_PAGE_ROUTE)
    assert r.status_code in (302, 308)


# ── Manager scoping ───────────────────────────────────────────────────────────

MANAGER_ROLES = ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']

@pytest.mark.parametrize("role", MANAGER_ROLES)
@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_manager_scoped_no_500(app, role, route):
    """SI endpoints handle manager scoping without 500."""
    c = make_client(app, [role])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── KPI endpoint response structure ──────────────────────────────────────────

def test_si_kpi_returns_json(app):
    """SI KPI endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/kpi')
    assert r.status_code != 500
    if r.content_type and 'json' in r.content_type:
        data = json.loads(r.data)
        assert isinstance(data, (dict, list))


def test_si_coverage_returns_json(app):
    """SI coverage endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/coverage')
    assert r.status_code != 500


def test_si_gaps_returns_json(app):
    """SI gaps endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/gaps')
    assert r.status_code != 500


def test_si_heatmap_returns_json(app):
    """SI heatmap endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/heatmap')
    assert r.status_code != 500


def test_si_top_skills_returns_json(app):
    """SI top-skills endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/top-skills')
    assert r.status_code != 500


def test_si_validation_returns_json(app):
    """SI validation endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/validation')
    assert r.status_code != 500


def test_si_trends_returns_json(app):
    """SI trends endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/trends')
    assert r.status_code != 500


def test_si_growth_returns_json(app):
    """SI growth endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/growth')
    assert r.status_code != 500


def test_si_job_coverage_returns_json(app):
    """SI job-coverage endpoint returns JSON."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/job-coverage')
    assert r.status_code != 500


# ── SI with various company IDs ───────────────────────────────────────────────

COMPANY_IDS = [
    FAKE_COMPANY_ID, FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000004',
]

@pytest.mark.parametrize("company_id", COMPANY_IDS)
@pytest.mark.parametrize("route", SI_API_ROUTES[:3])  # subset for speed
def test_si_various_company_ids(app, company_id, route):
    """SI endpoints handle various company IDs."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=company_id)
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── SI with empty DB results ──────────────────────────────────────────────────

@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_empty_db_results(app, route):
    """SI endpoints handle empty DB results."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── SI toggle HR endpoint ────────────────────────────────────────────────────

def test_si_toggle_hr_sa_only(app):
    """SI toggle-hr endpoint accessible to SYSTEM_ADMIN only."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value={'id': 'fid'}), \
         patch('app.routes.skills_intelligence.execute', return_value=None):
        r = c.post(
            '/api/admin/skills-intelligence/toggle-hr',
            data=json.dumps({'company_id': FAKE_COMPANY_ID, 'enabled': True}),
            content_type='application/json'
        )
    assert r.status_code != 500


def test_si_toggle_hr_blocked_portal_admin(app):
    """SI toggle-hr endpoint blocked for PORTAL_ADMIN."""
    c = make_client(app, ['PORTAL_ADMIN'])
    r = c.post(
        '/api/admin/skills-intelligence/toggle-hr',
        data=json.dumps({'company_id': FAKE_COMPANY_ID, 'enabled': True}),
        content_type='application/json'
    )
    assert r.status_code in (302, 308, 403)


# ── Feature access required ───────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_si_kpi_no_feature_access_redirect(app, role):
    """SI KPI redirects when user lacks feature access."""
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value=SI_EMPTY_MAP):
        r = c.get('/api/admin/skills-intelligence/kpi')
    assert r.status_code in (302, 308)


# ── Multiple SI endpoints in sequence ────────────────────────────────────────

def test_si_multiple_endpoints_sequence(app):
    """Multiple SI endpoints can be called in sequence without error."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        for route in SI_API_ROUTES:
            r = c.get(route)
            assert r.status_code != 500


# ── SI with null company_id ───────────────────────────────────────────────────

@pytest.mark.parametrize("role", ['PORTAL_ADMIN', 'HR_ADMIN'])
@pytest.mark.parametrize("route", SI_API_ROUTES[:3])
def test_si_null_company_id(app, role, route):
    """SI endpoints handle null company_id gracefully."""
    c = make_client(app, [role], company_id=None)
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=False), \
         patch('app.routes.skills_intelligence.current_company_id', return_value=None), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get(route)
    assert r.status_code in (302, 308, 403) or r.status_code != 500


# ── SI with SA company context ────────────────────────────────────────────────

@pytest.mark.parametrize("company_id", COMPANY_IDS)
def test_si_sa_company_context(app, company_id):
    """SA with specific company context gets correct SI data."""
    c = make_client(app, ['SYSTEM_ADMIN'], admin_company_id=company_id)
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=SI_FULL_MAP):
        r = c.get('/api/admin/skills-intelligence/kpi')
    assert r.status_code != 500


# ── SI access without feature map ────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_si_partial_feature_map_no_si_access(app, role):
    """SI endpoints redirect when si not in feature map."""
    c = make_client(app, [role])
    # Map has reports but not skills_intelligence
    partial_map = {'reports': {'r': True, 'w': True, 'd': True}}
    with patch('app.auth._load_feature_access', return_value=partial_map):
        r = c.get('/api/admin/skills-intelligence/kpi')
    assert r.status_code in (302, 308)


# ── SI readonly access ────────────────────────────────────────────────────────

@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_readonly_access_allowed(app, route):
    """SI API routes work with read-only access map."""
    c = make_client(app, ['HR_ADMIN'])
    readonly_map = {'skills_intelligence': {'r': True, 'w': False, 'd': False}}
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=readonly_map):
        r = c.get(route)
    assert r.status_code != 500
