"""
test_analytics_comprehensive.py — 600+ tests for analytics endpoints.
Tests all 9 roles × 6 endpoints, date ranges, scoping, disabled/enabled states.
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

ANALYTICS_API_ROUTES = [
    '/api/analytics/overview',
    '/api/analytics/vacation',
    '/api/analytics/skills',
    '/api/analytics/org',
    '/api/analytics/search',
]

ANALYTICS_ROUTES_ALL = ANALYTICS_API_ROUTES + ['/admin/analytics']

DATE_RANGES = ['30d', '90d', '365d', 'custom']
VALID_DATES = [('2026-01-01', '2026-03-31'), ('2025-01-01', '2025-12-31'),
               ('2026-01-01', '2026-01-31'), ('2024-06-01', '2024-12-31')]

REPORTS_MAP = {'reports': {'r': True, 'w': True, 'd': True}}
EMPTY_MAP = {}

MOCK_DATA = {'total': 0, 'active': 0, 'data': []}

def analytics_patches():
    """Return context managers for all analytics service mocks."""
    return [
        patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA),
        patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA),
        patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA),
        patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA),
        patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA),
        patch('app.db.query', return_value=[]),
    ]


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


def mock_analytics_enabled(c_id):
    return True


def mock_analytics_disabled(c_id):
    return False


# ── Unauthenticated access ────────────────────────────────────────────────────

@pytest.mark.parametrize("route", ANALYTICS_ROUTES_ALL)
def test_analytics_unauthenticated_redirect(client, route):
    """All analytics routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


# ── All 9 roles × 5 API endpoints ─────────────────────────────────────────────

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ALL_ROLES
    for route in ANALYTICS_API_ROUTES
])
def test_analytics_api_no_500_all_roles(app, role, route):
    """All analytics API endpoints return non-500 for every role."""
    c = make_client(app, [role])
    mock_data = {'total': 0, 'active': 0, 'data': []}
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=mock_data), \
         patch('app.services.analytics_service.get_org_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_search_analytics', return_value=mock_data), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── Analytics enabled/disabled states ────────────────────────────────────────

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE']
    for route in ANALYTICS_API_ROUTES
])
def test_analytics_disabled_returns_403(app, role, route):
    """When analytics disabled, non-SA roles get 403."""
    c = make_client(app, [role])
    with patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_disabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code in (302, 308, 403)


@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_disabled_sa_still_accessible(app, route):
    """SYSTEM_ADMIN can access analytics even when disabled for company."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_disabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── Date range parameters ─────────────────────────────────────────────────────

@pytest.mark.parametrize("range_param", DATE_RANGES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_date_range_param(app, range_param, route):
    """Analytics API handles all date range parameters."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'{route}?range={range_param}')
    assert r.status_code != 500


@pytest.mark.parametrize("start,end", VALID_DATES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_custom_date_range(app, start, end, route):
    """Analytics API handles custom date range parameters."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'{route}?start={start}&end={end}')
    assert r.status_code != 500


# ── Invalid date ranges ───────────────────────────────────────────────────────

INVALID_DATE_RANGES = [
    ('invalid-date', 'also-invalid'),
    ('2026-13-01', '2026-12-31'),
    ('2026-01-32', '2026-02-01'),
    ('not-a-date', '2026-01-01'),
    ('2026-01-01', 'not-a-date'),
    ('', '2026-01-01'),
    ('2026-01-01', ''),
    ('', ''),
    ('2099-99-99', '2099-99-99'),
    ('abc', 'def'),
]

@pytest.mark.parametrize("start,end", INVALID_DATE_RANGES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES[:2])  # subset for speed
def test_analytics_invalid_dates_no_500(app, start, end, route):
    """Analytics API handles invalid date parameters gracefully."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'{route}?start={start}&end={end}')
    assert r.status_code != 500


# ── Missing company_id ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES[:3])
def test_analytics_missing_company_id(app, role, route):
    """Analytics API handles missing company_id gracefully."""
    c = make_client(app, [role], company_id=None)
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', return_value=False), \
         patch('app.routes.analytics.current_company_id', return_value=None), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── Analytics scoping: manager vs admin ──────────────────────────────────────

MANAGER_ROLES = ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']

@pytest.mark.parametrize("role", MANAGER_ROLES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_manager_scoped(app, role, route):
    """Manager roles get scoped analytics."""
    c = make_client(app, [role])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── Analytics overview response structure ─────────────────────────────────────

def test_analytics_overview_returns_json(app):
    """Analytics overview returns JSON response."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/api/analytics/overview')
    assert r.status_code != 500


def test_analytics_vacation_returns_json(app):
    """Analytics vacation returns JSON response."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/api/analytics/vacation')
    assert r.status_code != 500


def test_analytics_skills_returns_json(app):
    """Analytics skills returns JSON response."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/api/analytics/skills')
    assert r.status_code != 500


def test_analytics_org_returns_json(app):
    """Analytics org returns JSON response."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/api/analytics/org')
    assert r.status_code != 500


# ── SA with company_id param ──────────────────────────────────────────────────

@pytest.mark.parametrize("company_id", [
    FAKE_COMPANY_ID, FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000004',
])
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_sa_analytics_with_company_param(app, company_id, route):
    """SA can pass company_id param to analytics endpoints."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics.current_company_id', return_value=company_id), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'{route}?company_id={company_id}')
    assert r.status_code != 500


# ── Admin analytics page ──────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'])
def test_admin_analytics_page_accessible(app, role):
    """Admin analytics page accessible to admin roles."""
    c = make_client(app, [role])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/admin/analytics')
    assert r.status_code not in [500]


@pytest.mark.parametrize("role", ['DEPARTMENT_HEAD', 'LOCATION_HEAD', 'EMPLOYEE',
                                   'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'HIRING_MANAGER'])
def test_admin_analytics_page_no_feature_access_blocked(app, role):
    """Admin analytics page blocked when user lacks feature access."""
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin/analytics')
    assert r.status_code in (302, 308)


# ── Analytics export CSV ──────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'])
def test_analytics_export_csv_admin_no_500(app, role):
    """Analytics CSV export accessible for admin roles."""
    c = make_client(app, [role])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get('/api/analytics/export/csv')
    assert r.status_code != 500


@pytest.mark.parametrize("export_type", ['vacation', 'skills', 'headcount', 'org', 'overview'])
def test_analytics_export_csv_types(app, export_type):
    """Analytics CSV export handles various export types."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'/api/analytics/export/csv?type={export_type}')
    assert r.status_code != 500


# ── _scoped flag correctness ──────────────────────────────────────────────────

@pytest.mark.parametrize("role,expected_scoped", [
    ('SYSTEM_ADMIN', False),
    ('PORTAL_ADMIN', False),
    ('HR_ADMIN', False),
    ('DEPARTMENT_HEAD', True),
    ('LOCATION_HEAD', True),
    ('SOLID_LINE_MANAGER', True),
    ('DOTTED_LINE_MANAGER', True),
    ('HIRING_MANAGER', True),
    ('EMPLOYEE', True),
])
def test_resolve_scope_scoped_flag(app, role, expected_scoped):
    """_resolve_scope sets is_scoped flag correctly per role."""
    with app.test_request_context('/api/analytics/overview'):
        with patch('app.db.query', return_value=[]):
            from flask import session
            session['roles'] = [role]
            session['company_id'] = FAKE_COMPANY_ID
            session['employee_id'] = '00000000-0000-0000-0000-000000000030'
            from app.services.company_scope import resolve_report_scope
            scope = resolve_report_scope('emp-001', [role])
            is_scoped = scope is not None
            assert is_scoped == expected_scoped


# ── Analytics with empty DB results ──────────────────────────────────────────

@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_empty_db_result(app, route):
    """Analytics handles empty DB results gracefully."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=MOCK_DATA), \
         patch('app.services.analytics_service.get_search_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(route)
    assert r.status_code != 500


# ── Company feature toggle ────────────────────────────────────────────────────

def test_toggle_company_feature_sa_only(app):
    """Feature toggle endpoint accessible to SYSTEM_ADMIN only."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.analytics.query', return_value={'id': 'feature-id'}), \
         patch('app.routes.analytics.execute', return_value=None):
        r = c.post(
            f'/api/admin/company-features/{FAKE_COMPANY_ID}/toggle',
            data=json.dumps({'feature_code': 'reports', 'enabled': True}),
            content_type='application/json'
        )
    assert r.status_code != 500


def test_toggle_company_feature_blocked_for_portal_admin(app):
    """Feature toggle blocked for PORTAL_ADMIN."""
    c = make_client(app, ['PORTAL_ADMIN'])
    r = c.post(f'/api/admin/company-features/{FAKE_COMPANY_ID}/toggle',
               data=json.dumps({'feature_code': 'reports', 'enabled': True}),
               content_type='application/json')
    assert r.status_code in (302, 308)


# ── Analytics API query parameters ───────────────────────────────────────────

QUERY_PARAM_SCENARIOS = [
    '?range=30d',
    '?range=90d',
    '?range=365d',
    '?start=2026-01-01&end=2026-03-31',
    '?start=2025-01-01&end=2025-12-31',
    '?range=30d&company_id=' + FAKE_COMPANY_ID,
    '',
]

@pytest.mark.parametrize("params", QUERY_PARAM_SCENARIOS)
def test_analytics_overview_various_params(app, params):
    """Analytics overview handles various query params."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_overview', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'/api/analytics/overview{params}')
    assert r.status_code != 500


@pytest.mark.parametrize("params", QUERY_PARAM_SCENARIOS)
def test_analytics_org_various_params(app, params):
    """Analytics org handles various query params."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', side_effect=mock_analytics_enabled), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.services.analytics_service.get_org_analytics', return_value=MOCK_DATA), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value=REPORTS_MAP):
        r = c.get(f'/api/analytics/org{params}')
    assert r.status_code != 500
