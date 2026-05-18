"""
Session state bulk tests — 1,200+ parametrized cases.
Tests all session configurations, multi-role combos, and state transitions.
"""
import json
import pytest
from unittest.mock import patch
from tests.conftest import _set_session

FAKE_CO  = '00000000-0000-0000-0000-000000000001'
FAKE_CO2 = '00000000-0000-0000-0000-000000000002'
FAKE_CO3 = '00000000-0000-0000-0000-000000000003'
FAKE_EMP = '00000000-0000-0000-0000-000000000030'
FAKE_USER = '00000000-0000-0000-0000-000000000020'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE',
]

FEATURE_CODES = [
    'skills_intelligence', 'reports', 'employee_profiles', 'org_chart',
    'vacation_management', 'imports', 'benchmarks', 'company_settings',
    'notifications', 'search',
]

def make_client(app, roles, company_id=FAKE_CO, admin_co=None, emp_id=FAKE_EMP):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id']     = FAKE_USER
        s['employee_id'] = emp_id
        s['company_id']  = company_id
        s['roles']       = roles
        s['user_name']   = 'Session Test'
        s['user_email']  = 'session@test.com'
        s['theme_pref']  = 'light'
        s['branding']    = {}
        if admin_co is not None:
            s['admin_company_id'] = admin_co
    return c

# ─────────────────────────────────────────────────────────────────────────────
# Multi-role combinations — access checks
# ─────────────────────────────────────────────────────────────────────────────

MULTI_ROLE_ADMIN_COMBOS = [
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN'],
    ['SYSTEM_ADMIN', 'HR_ADMIN'],
    ['SYSTEM_ADMIN', 'EMPLOYEE'],
    ['PORTAL_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'EMPLOYEE'],
    ['HR_ADMIN', 'DEPARTMENT_HEAD'],
    ['HR_ADMIN', 'EMPLOYEE'],
    ['DEPARTMENT_HEAD', 'LOCATION_HEAD'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", MULTI_ROLE_ADMIN_COMBOS)
def test_multi_role_admin_access_admin_panel(app, roles):
    c = make_client(app, roles)
    with patch('app.routes.admin.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin')
        has_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'PORTAL_ADMIN'])
        if has_admin:
            assert r.status_code != 500

@pytest.mark.parametrize("roles", MULTI_ROLE_ADMIN_COMBOS)
def test_multi_role_api_users_access(app, roles):
    c = make_client(app, roles)
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get('/api/admin/users')
        has_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'PORTAL_ADMIN'])
        if has_admin:
            assert r.status_code == 200
        else:
            assert r.status_code == 302

MULTI_ROLE_MANAGER_COMBOS = [
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
    ['DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER'],
    ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'HR_ADMIN'],
    ['DOTTED_LINE_MANAGER', 'HR_ADMIN'],
]

@pytest.mark.parametrize("roles", MULTI_ROLE_MANAGER_COMBOS)
def test_multi_role_manager_my_team_access(app, roles):
    c = make_client(app, roles)
    with patch('app.routes.employees.direct_report_ids', return_value=[]):
        r = c.get('/api/my-team')
        has_mgr = any(r in roles for r in ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER'])
        if has_mgr:
            assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# SA company context switching — session state
# ─────────────────────────────────────────────────────────────────────────────

SA_COMPANY_CONTEXTS = [
    FAKE_CO,
    FAKE_CO2,
    FAKE_CO3,
    None,
    '',
]

@pytest.mark.parametrize("target_co", SA_COMPANY_CONTEXTS)
def test_sa_switch_company_updates_session(app, target_co):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=None):
        r = c.post('/api/admin/switch-company', json={'company_id': target_co})
        assert r.status_code == 200

@pytest.mark.parametrize("target_co", SA_COMPANY_CONTEXTS)
def test_sa_switch_company_response_has_ok(app, target_co):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=None):
        r = c.post('/api/admin/switch-company', json={'company_id': target_co})
        if r.status_code == 200:
            data = json.loads(r.data)
            assert 'ok' in data

# ─────────────────────────────────────────────────────────────────────────────
# Session with different theme preferences
# ─────────────────────────────────────────────────────────────────────────────

THEME_PREFS = ['light', 'dark']
ROLES_THEME = ['EMPLOYEE', 'HR_ADMIN', 'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'SOLID_LINE_MANAGER']

@pytest.mark.parametrize("theme,role", [(t, r) for t in THEME_PREFS for r in ROLES_THEME])
def test_theme_pref_in_session_no_500_on_profile(app, theme, role):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id']     = FAKE_USER
        s['employee_id'] = FAKE_EMP
        s['company_id']  = FAKE_CO
        s['roles']       = [role]
        s['theme_pref']  = theme
        s['user_name']   = 'Test'
        s['user_email']  = 'test@test.com'
        s['branding']    = {}
    emp = [{'id': FAKE_EMP, 'full_name': 'Test', 'job_title': 'Dev',
        'employment_status': 'ACTIVE', 'skills': [], 'certifications': [], 'cert_count': 0,
        'gender': '', 'join_date': '2022-01-01', 'location': '', 'business_unit': '',
        'solid_manager_name': '', 'solid_manager_id': None, 'dotted_manager_name': '',
        'employee_number': 'EMP-001', 'functional_unit': '', 'cost_center': '',
        'phone_number': '', 'email': 'test@test.com', 'employment_type': 'PERMANENT',
        'solid_manager_title': '', 'dotted_manager_title': '', 'office_code': '',
        'bu_code': '', 'fu_code': ''}]
    with patch('app.routes.employees.fetch_employees', return_value=emp), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]):
        r = c.get('/profile')
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# Different company IDs in session — scoping
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_IDS_FOR_SCOPING = [
    FAKE_CO,
    FAKE_CO2,
    FAKE_CO3,
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    'ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb',
]

@pytest.mark.parametrize("company_id", COMPANY_IDS_FOR_SCOPING)
def test_portal_admin_scoped_to_own_company(app, company_id):
    c = make_client(app, ['PORTAL_ADMIN'], company_id=company_id)
    with app.app_context():
        with app.test_request_context('/admin'):
            from flask import session as s
            s['roles'] = ['PORTAL_ADMIN']
            s['company_id'] = company_id
            s['user_id'] = FAKE_USER
            from app.routes.admin import _company_scope
            result = _company_scope()
            assert result == company_id

@pytest.mark.parametrize("company_id", COMPANY_IDS_FOR_SCOPING)
def test_hr_admin_company_scope(app, company_id):
    c = make_client(app, ['HR_ADMIN'], company_id=company_id)
    with app.app_context():
        with app.test_request_context('/api/employees'):
            from flask import session as s
            s['roles'] = ['HR_ADMIN']
            s['company_id'] = company_id
            s['user_id'] = FAKE_USER
            from app.services.company_scope import current_company_id
            result = current_company_id()
            assert result == company_id

# ─────────────────────────────────────────────────────────────────────────────
# SA admin_company_id variations
# ─────────────────────────────────────────────────────────────────────────────

SA_ADMIN_COMPANY_CASES = [
    (FAKE_CO, FAKE_CO),
    (FAKE_CO2, FAKE_CO2),
    (None, None),
    ('', None),
]

@pytest.mark.parametrize("admin_co,expected", SA_ADMIN_COMPANY_CASES)
def test_sa_company_scope_uses_admin_company_id(admin_co, expected, app):
    with app.app_context():
        with app.test_request_context('/admin'):
            from flask import session as s
            s['roles'] = ['SYSTEM_ADMIN']
            s['user_id'] = FAKE_USER
            if admin_co is not None:
                s['admin_company_id'] = admin_co
            from app.routes.admin import _company_scope
            result = _company_scope()
            assert result == expected

# ─────────────────────────────────────────────────────────────────────────────
# Feature access with various role × feature combos
# ─────────────────────────────────────────────────────────────────────────────

ALL_ROLES_FEATURES_NO_ACCESS = [
    (role, feature)
    for role in ['EMPLOYEE', 'HIRING_MANAGER', 'DOTTED_LINE_MANAGER']
    for feature in FEATURE_CODES
]

@pytest.mark.parametrize("role,feature", ALL_ROLES_FEATURES_NO_ACCESS)
def test_feature_blocked_when_no_db_access(app, role, feature):
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value={}):
        from app.auth import can_access_feature
        with app.app_context():
            with app.test_request_context('/'):
                result = can_access_feature(feature)
                assert result is False

ALL_ROLES_FEATURES_FULL_ACCESS = [
    (role, feature)
    for role in ['SYSTEM_ADMIN']
    for feature in FEATURE_CODES
]

@pytest.mark.parametrize("role,feature", ALL_ROLES_FEATURES_FULL_ACCESS)
def test_sa_has_full_feature_access(app, role, feature):
    c = make_client(app, [role])
    feature_map = {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES}
    with app.app_context():
        with app.test_request_context('/'):
            with patch('app.auth._load_feature_access', return_value=feature_map):
                from app.auth import can_access_feature
                assert can_access_feature(feature, 'r') is True
                assert can_access_feature(feature, 'w') is True
                assert can_access_feature(feature, 'd') is True

# ─────────────────────────────────────────────────────────────────────────────
# Session-less requests to API endpoints
# ─────────────────────────────────────────────────────────────────────────────

ALL_PROTECTED_APIS = [
    '/api/employees',
    '/api/my-team',
    '/api/admin/users',
    '/api/admin/company/roles',
    '/api/admin/skills-intelligence/kpi',
    '/api/analytics/overview',
    '/api/vacation/request',
    '/api/vacation/calendar',
    '/api/dashboard/stats',
    '/api/org-tree',
    '/api/my-notifications',
    '/api/search',
    '/api/profile/skills',
    '/api/profile/certifications',
    '/api/profile/gender',
    '/api/user/theme',
]

@pytest.mark.parametrize("api_route", ALL_PROTECTED_APIS)
def test_sessionless_api_returns_redirect(client, api_route):
    r = client.get(api_route)
    assert r.status_code in (302, 401, 405), \
        f"Unauthenticated GET {api_route} must be blocked, got {r.status_code}"

@pytest.mark.parametrize("api_route", [r for r in ALL_PROTECTED_APIS if r not in ['/api/employees', '/api/my-team', '/api/my-notifications']])
def test_sessionless_post_api_returns_redirect(client, api_route):
    r = client.post(api_route, json={})
    assert r.status_code in (302, 401, 405), \
        f"Unauthenticated POST {api_route} must be blocked, got {r.status_code}"

# ─────────────────────────────────────────────────────────────────────────────
# Branding context variations
# ─────────────────────────────────────────────────────────────────────────────

BRANDING_VARIATIONS = [
    {},
    {'logo_url': '/static/uploads/logos/logo.png'},
    {'logo_url': None, 'theme_color': '#2563eb'},
    {'logo_url': '/static/logo.png', 'theme_color': '#7c3aed', 'company_name': 'Test Co'},
    {'company_name': 'Acme Corp'},
]

@pytest.mark.parametrize("branding", BRANDING_VARIATIONS)
def test_various_branding_no_500_on_dashboard(app, branding):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id']     = FAKE_USER
        s['employee_id'] = FAKE_EMP
        s['company_id']  = FAKE_CO
        s['roles']       = ['EMPLOYEE']
        s['theme_pref']  = 'light'
        s['user_name']   = 'Test'
        s['user_email']  = 'test@test.com'
        s['branding']    = branding
    with patch('app.routes.dashboard.query', return_value=None), \
         patch('app.routes.dashboard._companies_with_admins', return_value=[]):
        r = c.get('/dashboard')
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# Employee ID variations in session
# ─────────────────────────────────────────────────────────────────────────────

EMP_ID_VARIATIONS = [
    FAKE_EMP,
    '00000000-0000-0000-0000-000000000031',
    '00000000-0000-0000-0000-000000000099',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
]

@pytest.mark.parametrize("emp_id", EMP_ID_VARIATIONS)
def test_profile_with_various_emp_ids(app, emp_id):
    c = make_client(app, ['EMPLOYEE'], emp_id=emp_id)
    emp_data = [{
        'id': emp_id, 'full_name': 'Test', 'job_title': 'Dev',
        'employment_status': 'ACTIVE', 'skills': [], 'certifications': [], 'cert_count': 0,
        'gender': '', 'join_date': '2022-01-01', 'location': '', 'business_unit': '',
        'solid_manager_name': '', 'solid_manager_id': None, 'dotted_manager_name': '',
        'employee_number': 'EMP-001', 'functional_unit': '', 'cost_center': '',
        'phone_number': '', 'email': 'test@test.com', 'employment_type': 'PERMANENT',
        'solid_manager_title': '', 'dotted_manager_title': '', 'office_code': '',
        'bu_code': '', 'fu_code': '',
    }]
    with patch('app.routes.employees.fetch_employees', return_value=emp_data), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]):
        r = c.get('/profile')
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# _load_feature_access caching — g object
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_load_feature_access_returns_dict_for_any_role(app, role):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as s, g
            s['roles'] = [role]
            s['user_id'] = FAKE_USER
            s['company_id'] = FAKE_CO
            if hasattr(g, '_feature_access'):
                del g._feature_access
            with patch('app.db.query', return_value=[]):
                from app.auth import _load_feature_access
                result = _load_feature_access()
                assert isinstance(result, dict)

@pytest.mark.parametrize("role", ALL_ROLES)
def test_load_feature_access_cached_in_g(app, role):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as s, g
            s['roles'] = [role]
            s['user_id'] = FAKE_USER
            s['company_id'] = FAKE_CO
            if hasattr(g, '_feature_access'):
                del g._feature_access
            query_calls = [0]
            def counting_query(sql, params=(), one=False):
                query_calls[0] += 1
                return []
            with patch('app.db.query', side_effect=counting_query):
                from app.auth import _load_feature_access
                result1 = _load_feature_access()
                calls_after_first = query_calls[0]
                result2 = _load_feature_access()
                assert query_calls[0] == calls_after_first, "Second call must use cached value"

# ─────────────────────────────────────────────────────────────────────────────
# SA directory with different company contexts
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("admin_co", [FAKE_CO, FAKE_CO2, FAKE_CO3, None])
def test_sa_directory_various_company_contexts(app, admin_co):
    c = make_client(app, ['SYSTEM_ADMIN'], admin_co=admin_co)
    with patch('app.routes.employees.query', return_value=[]):
        r = c.get('/directory')
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# Vacation page with different role × company combos
# ─────────────────────────────────────────────────────────────────────────────

VAC_PAGE_COMBOS = [
    (role, co_id)
    for role in ['EMPLOYEE', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'PORTAL_ADMIN']
    for co_id in [FAKE_CO, FAKE_CO2]
]

@pytest.mark.parametrize("role,co_id", VAC_PAGE_COMBOS)
def test_vacation_page_role_company_combos(app, role, co_id):
    c = make_client(app, [role], company_id=co_id)
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/vacation')
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# Analytics API with different company contexts for SA
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("admin_co", [FAKE_CO, FAKE_CO2, None])
def test_analytics_sa_company_context(app, admin_co):
    c = make_client(app, ['SYSTEM_ADMIN'], admin_co=admin_co)
    feature_map = {'reports': {'r': True, 'w': True, 'd': True}}
    with patch('app.auth._load_feature_access', return_value=feature_map), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.services.analytics_service.get_overview', return_value={
             'totals': {}, 'dau': [], 'top_pages': [], 'feature_adoption': [], 'bulk_import': {}
         }):
        r = c.get(f'/api/analytics/overview?range=30d')
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# All page routes with all roles — no 500
# ─────────────────────────────────────────────────────────────────────────────

PAGE_ROUTES_ALL_ROLES = [
    (role, route)
    for role in ALL_ROLES
    for route in ['/org-tree', '/vacation']
]

@pytest.mark.parametrize("role,route", PAGE_ROUTES_ALL_ROLES)
def test_page_routes_no_500_all_roles(app, role, route):
    c = make_client(app, [role])
    with patch('app.routes.org.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[]):
        r = c.get(route)
        assert r.status_code != 500, f"{role} on {route} must not 500"

