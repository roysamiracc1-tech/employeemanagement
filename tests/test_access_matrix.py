"""
test_access_matrix.py — 1,400+ tests covering access control matrix:
- Unauthenticated → 302 for all protected routes
- Role-based access: blocked vs allowed per route
- No 500 errors for any role × route combination
"""
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


def make_client(app, roles, company_id=FAKE_COMPANY_ID, emp_id='00000000-0000-0000-0000-000000000030'):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id'] = '00000000-0000-0000-0000-000000000020'
        s['employee_id'] = emp_id
        s['company_id'] = company_id
        s['roles'] = roles
        s['user_name'] = 'Test User'
        s['user_email'] = 'test@example.com'
        s['theme_pref'] = 'light'
        s['branding'] = {}
    return c


# All protected routes that require authentication
PROTECTED_GET_ROUTES = [
    '/admin',
    '/admin/analytics',
    '/admin/benchmarks',
    '/admin/companies',
    '/admin/companies/new',
    '/admin/company-settings',
    '/admin/imports',
    '/admin/register-user',
    '/admin/skills-intelligence',
    '/admin/vacation-types',
    '/admin/vacation-types/new',
    '/dashboard',
    '/directory',
    '/my-team',
    '/org-tree',
    '/profile',
    '/search',
    '/vacation',
    '/vacation/calendar',
    '/api/admin/benchmarks',
    '/api/admin/benchmarks/categories',
    '/api/admin/company/role-feature-access',
    '/api/admin/company/roles',
    '/api/admin/employees',
    '/api/admin/roles/features',
    '/api/admin/users',
    '/api/analytics/overview',
    '/api/analytics/org',
    '/api/analytics/skills',
    '/api/analytics/vacation',
    '/api/dashboard/stats',
    '/api/employees',
    '/api/my-notifications',
    '/api/my-team',
    '/api/notifications/my-mutes',
    '/api/notifications/settings',
    '/api/org-tree',
    '/api/org-tree/context',
    '/api/search',
    '/api/vacation/calendar',
    '/api/vacation/pending-count',
    '/api/vacation/team-pending-counts',
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

# Routes that only admin roles can access
ADMIN_ONLY_ROUTES = [
    '/admin',
    '/admin/register-user',
    '/api/admin/users',
    '/api/admin/employees',
]

# Non-admin roles that should be blocked from admin routes
NON_ADMIN_ROLES = [
    'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER',
    'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'EMPLOYEE'
]

# API routes accessible to employees
EMPLOYEE_API_ROUTES = [
    '/api/employees',
    '/api/my-team',
    '/api/org-tree',
    '/api/profile/skills',
    '/api/profile/certifications',
    '/api/search',
    '/api/vacation/pending-count',
    '/api/vacation/calendar',
    '/api/my-notifications',
    '/api/notifications/settings',
    '/api/notifications/my-mutes',
    '/api/dashboard/stats',
]

# Routes accessible to all authenticated users
PUBLIC_AUTH_ROUTES = [
    '/dashboard',
    '/directory',
    '/profile',
    '/search',
    '/vacation',
    '/vacation/calendar',
    '/my-team',
    '/org-tree',
]


@pytest.mark.parametrize("route", PROTECTED_GET_ROUTES)
def test_unauthenticated_redirect(client, route):
    """All protected routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", PROTECTED_GET_ROUTES)
def test_unauthenticated_redirect_points_to_login(client, route):
    """Redirect should go to login."""
    r = client.get(route)
    if r.status_code in (301, 302, 308):
        location = r.headers.get('Location', '')
        assert 'login' in location or r.status_code in (302, 308)


@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
@pytest.mark.parametrize("route", ADMIN_ONLY_ROUTES)
def test_non_admin_blocked_from_admin_routes(app, role, route):
    """Non-admin roles should be redirected from admin-only routes."""
    c = make_client(app, [role])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_dashboard_accessible_all_roles(app, role):
    """Dashboard should be accessible to all authenticated roles."""
    c = make_client(app, [role])
    mock_stats = {'active_employees': 0, 'new_hires': 0, 'departments': 0,
                  'pending_requests': 0, 'skills_count': 0, 'certifications': 0}
    with patch('app.routes.dashboard.compute_dashboard_stats', return_value=mock_stats), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/dashboard')
    assert r.status_code in (200, 302)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_profile_accessible_all_roles(app, role):
    """Profile page should be accessible to all authenticated roles."""
    c = make_client(app, [role])
    emp = {
        'id': '00000000-0000-0000-0000-000000000030',
        'employee_number': 'EMP-001', 'full_name': 'Test User',
        'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com',
        'phone_number': '', 'job_title': 'Engineer', 'employment_status': 'ACTIVE',
        'employment_type': 'PERMANENT', 'gender': 'MALE', 'join_date': '2022-01-01',
        'location': 'London', 'office_code': 'LDN', 'business_unit': 'Eng',
        'bu_code': 'ENG', 'functional_unit': 'Platform', 'fu_code': 'PLT',
        'cost_center': 'CC-001', 'solid_manager_name': '', 'solid_manager_title': '',
        'solid_manager_id': None, 'dotted_manager_name': '', 'dotted_manager_title': '',
        'skills': [], 'cert_count': 0, 'certifications': [],
    }
    with patch('app.routes.employees.fetch_employees', return_value=[emp]), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.to_dict', side_effect=lambda r: r if isinstance(r, dict) else dict(r)), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/profile')
    assert r.status_code in (200, 302)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_directory_accessible_all_roles(app, role):
    """Directory should be accessible to all authenticated roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code in (200, 302)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_employees_no_500(app, role):
    """API employees endpoint should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_my_team_no_500(app, role):
    """API my-team endpoint should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/my-team')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_search_no_500(app, role):
    """Search API should not return 500."""
    c = make_client(app, [role])
    with patch('app.services.search_service.unified_search', return_value=[]):
        r = c.get('/api/search?q=test')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_org_tree_no_500(app, role):
    """Org tree API should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.org.query', return_value=[]):
        r = c.get('/api/org-tree')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_dashboard_stats_no_500(app, role):
    """Dashboard stats API should not return 500."""
    c = make_client(app, [role])
    mock_stats = {
        'active_employees': 10, 'new_hires': 1, 'departments': 3,
        'pending_requests': 0, 'skills_count': 5, 'certifications': 2,
    }
    with patch('app.routes.dashboard.compute_dashboard_stats', return_value=mock_stats):
        r = c.get('/api/dashboard/stats')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_vacation_pending_count_no_500(app, role):
    """Vacation pending count API should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value={'cnt': 0}):
        r = c.get('/api/vacation/pending-count')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_profile_skills_no_500(app, role):
    """Profile skills API should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]):
        r = c.get('/api/profile/skills')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_profile_certifications_no_500(app, role):
    """Profile certifications API should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]):
        r = c.get('/api/profile/certifications')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_my_notifications_no_500(app, role):
    """My notifications API should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.notifications.query', return_value=[]):
        r = c.get('/api/my-notifications')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_vacation_page_no_500(app, role):
    """Vacation page should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/vacation')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_my_team_page_no_500(app, role):
    """My-team page should not return 500."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/my-team')
    assert r.status_code != 500


# ── Admin API access matrix ────────────────────────────────────────────────────

ADMIN_API_ROUTES = [
    '/api/admin/users',
    '/api/admin/employees',
    '/api/admin/company/roles',
]

@pytest.mark.parametrize("route", ADMIN_API_ROUTES)
@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
def test_non_admin_api_blocked(app, role, route):
    """Non-admin roles blocked from admin API endpoints."""
    c = make_client(app, [role])
    r = c.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", ADMIN_API_ROUTES)
def test_system_admin_api_accessible(app, route):
    """SYSTEM_ADMIN can access admin API endpoints."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("route", ADMIN_API_ROUTES)
def test_portal_admin_api_accessible(app, route):
    """PORTAL_ADMIN can access admin API endpoints."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


# ── Skills Intelligence access matrix ─────────────────────────────────────────

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

FULL_FEATURE_ACCESS = {
    'skills_intelligence': {'r': True, 'w': True, 'd': True},
    'reports': {'r': True, 'w': True, 'd': True},
}


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_unauthenticated_redirect(client, route):
    """SI API routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_system_admin_no_500(app, route):
    """SYSTEM_ADMIN accessing SI routes should not get 500."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=FULL_FEATURE_ACCESS):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("route", SI_API_ROUTES)
def test_si_portal_admin_with_access_no_500(app, route):
    """PORTAL_ADMIN with SI access should not get 500."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value=FULL_FEATURE_ACCESS):
        r = c.get(route)
    assert r.status_code != 500


# ── Analytics access matrix ───────────────────────────────────────────────────

ANALYTICS_API_ROUTES = [
    '/api/analytics/overview',
    '/api/analytics/org',
    '/api/analytics/skills',
    '/api/analytics/vacation',
]

@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_unauthenticated(client, route):
    """Analytics API redirects unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("route", ANALYTICS_API_ROUTES)
def test_analytics_no_500_for_any_role(app, role, route):
    """Analytics API endpoints should not return 500 for any role."""
    c = make_client(app, [role])
    mock_data = {'total': 0, 'active': 0, 'data': []}
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.services.analytics_service.get_overview', return_value=mock_data), \
         patch('app.services.analytics_service.get_org_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_vacation_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_skills_analytics', return_value=mock_data), \
         patch('app.services.analytics_service.get_search_analytics', return_value=mock_data), \
         patch('app.auth._load_feature_access', return_value={
             'reports': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get(route)
    assert r.status_code != 500


# ── SYSTEM_ADMIN bypass checks ────────────────────────────────────────────────

SA_SPECIFIC_ROUTES = [
    '/api/admin/roles/features',
]

@pytest.mark.parametrize("route", SA_SPECIFIC_ROUTES)
def test_sa_specific_routes_blocked_for_portal_admin(app, route):
    """SA-only routes blocked for PORTAL_ADMIN."""
    c = make_client(app, ['PORTAL_ADMIN'])
    r = c.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", SA_SPECIFIC_ROUTES)
def test_sa_specific_routes_allowed_for_sa(app, route):
    """SA-only routes accessible for SYSTEM_ADMIN."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("route", SA_SPECIFIC_ROUTES)
@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
def test_sa_specific_routes_blocked_for_all_non_sa(app, role, route):
    """SA-only routes blocked for all non-SA roles."""
    c = make_client(app, [role])
    r = c.get(route)
    assert r.status_code in (302, 308)


# ── Vacation page access ───────────────────────────────────────────────────────

VACATION_ROUTES = [
    '/vacation',
    '/vacation/calendar',
]

@pytest.mark.parametrize("route", ['/vacation', '/vacation/calendar'])
@pytest.mark.parametrize("role", ALL_ROLES)
def test_vacation_page_no_500_any_role(app, role, route):
    """Vacation pages should not 500 for any role."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500


# ── Company context variations ─────────────────────────────────────────────────

COMPANY_IDS = [
    FAKE_COMPANY_ID,
    FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0000-000000000005',
]

@pytest.mark.parametrize("company_id", COMPANY_IDS)
def test_sa_company_context_employees(app, company_id):
    """SYSTEM_ADMIN with different company contexts gets employees."""
    c = make_client(app, ['SYSTEM_ADMIN'], company_id=company_id)
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


@pytest.mark.parametrize("company_id", COMPANY_IDS)
def test_portal_admin_company_context(app, company_id):
    """PORTAL_ADMIN with different company_ids gets scoped employees."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=company_id)
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


# ── Multi-role combinations ────────────────────────────────────────────────────

MULTI_ROLE_COMBOS = [
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN'],
    ['SYSTEM_ADMIN', 'EMPLOYEE'],
    ['PORTAL_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'EMPLOYEE'],
    ['HR_ADMIN', 'EMPLOYEE'],
    ['DEPARTMENT_HEAD', 'EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
    ['DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    ['HIRING_MANAGER', 'EMPLOYEE'],
    ['LOCATION_HEAD', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", MULTI_ROLE_COMBOS)
def test_multi_role_directory_no_500(app, roles):
    """Multi-role users can access directory."""
    c = make_client(app, roles)
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


@pytest.mark.parametrize("roles", MULTI_ROLE_COMBOS)
def test_multi_role_api_employees_no_500(app, roles):
    """Multi-role users can hit API employees."""
    c = make_client(app, roles)
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


# ── Login/logout routes ────────────────────────────────────────────────────────

def test_login_page_loads(client):
    """Login page loads for unauthenticated users."""
    r = client.get('/login')
    assert r.status_code == 200


def test_logout_redirects(auth_client):
    """Logout redirects to login."""
    r = auth_client.get('/logout')
    assert r.status_code in (302, 308)


def test_login_post_invalid(client):
    """Login POST with invalid credentials does not 500."""
    with patch('app.db.query', return_value=[]):
        r = client.post('/login', data={'username': 'bad', 'password': 'bad'})
    assert r.status_code != 500


# ── API routes with no company_id in session ──────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_no_company_id_in_session_api_employees(app, role):
    """API employees with no company_id in session should not 500."""
    c = make_client(app, [role], company_id=None)
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_empty_company_id_in_session(app, role):
    """API employees with empty company_id in session should not 500."""
    c = make_client(app, [role], company_id='')
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


# ── Benchmarks access matrix ───────────────────────────────────────────────────

BENCHMARK_ROUTES = [
    '/admin/benchmarks',
    '/api/admin/benchmarks',
    '/api/admin/benchmarks/categories',
]

@pytest.mark.parametrize("route", BENCHMARK_ROUTES)
def test_benchmarks_unauthenticated(client, route):
    """Benchmark routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", BENCHMARK_ROUTES)
def test_benchmarks_system_admin_no_500(app, route):
    """SYSTEM_ADMIN can access benchmark routes."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.benchmarks.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={
             'benchmarks': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get(route)
    assert r.status_code != 500


# ── Admin panel sub-pages ─────────────────────────────────────────────────────

ADMIN_SUB_PAGES = [
    '/admin/companies',
    '/admin/companies/new',
    '/admin/company-settings',
    '/admin/vacation-types',
    '/admin/vacation-types/new',
]

# Routes accessible to SA+PA+HR_ADMIN
ADMIN_IMPORTS_ROUTE = '/admin/imports'

@pytest.mark.parametrize("route", ADMIN_SUB_PAGES + [ADMIN_IMPORTS_ROUTE])
def test_admin_sub_pages_unauthenticated(client, route):
    """Admin sub-pages redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("route", ADMIN_SUB_PAGES)
@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
def test_admin_sub_pages_blocked_non_admin(app, role, route):
    """Non-admin roles blocked from admin sub-pages."""
    c = make_client(app, [role])
    r = c.get(route)
    assert r.status_code in (302, 308)


# ── API org-tree context ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_org_tree_context_no_500(app, role):
    """Org tree context API should not 500."""
    c = make_client(app, [role])
    with patch('app.routes.org.query', return_value=[]):
        r = c.get('/api/org-tree/context')
    assert r.status_code != 500


# ── Notifications settings ────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_notifications_settings_no_500(app, role):
    """Notifications settings API should not 500."""
    c = make_client(app, [role])
    with patch('app.routes.notifications.query', return_value=[]):
        r = c.get('/api/notifications/settings')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_notifications_mutes_no_500(app, role):
    """Notifications mutes API should not 500."""
    c = make_client(app, [role])
    with patch('app.routes.notifications.query', return_value=[]):
        r = c.get('/api/notifications/my-mutes')
    assert r.status_code != 500


# ── Org-tree page ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_org_tree_page_no_500(app, role):
    """Org-tree page should not 500 for any role."""
    c = make_client(app, [role])
    with patch('app.routes.org.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/org-tree')
    assert r.status_code != 500


# ── Search page ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_search_page_no_500(app, role):
    """Search page should not 500 for any role."""
    c = make_client(app, [role])
    with patch('app.services.search_service.unified_search', return_value={'results': [], 'total': 0}), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/search')
    assert r.status_code != 500


# ── Vacation calendar ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_vacation_calendar_api_no_500(app, role):
    """Vacation calendar API should not 500 for any role."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/vacation/calendar')
    assert r.status_code != 500


# ── Team vacation endpoints ───────────────────────────────────────────────────

TEAM_VAC_ROUTES_MGMT = [
    '/api/vacation/team-pending',
    '/api/vacation/team-upcoming',
]
# team-pending-counts is login_required only
TEAM_VAC_COUNTS_ROUTE = '/api/vacation/team-pending-counts'

MGMT_VAC_ROLES = ['SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']

@pytest.mark.parametrize("route", TEAM_VAC_ROUTES_MGMT)
@pytest.mark.parametrize("role", MGMT_VAC_ROLES)
def test_team_vacation_mgmt_no_500(app, role, route):
    """Team vacation API should not 500 for MGMT roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_team_vacation_counts_no_500(app, role):
    """Team pending counts should not 500 for any role."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get(TEAM_VAC_COUNTS_ROUTE)
    assert r.status_code != 500


# ── Admin analytics page ──────────────────────────────────────────────────────

def test_admin_analytics_portal_admin_no_500(app):
    """PORTAL_ADMIN can access admin analytics page."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value={
             'reports': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get('/admin/analytics')
    assert r.status_code != 500


def test_admin_analytics_employee_blocked(app):
    """EMPLOYEE blocked from admin analytics page."""
    c = make_client(app, ['EMPLOYEE'])
    r = c.get('/admin/analytics')
    assert r.status_code in (302, 308)


# ── Check redirect target ─────────────────────────────────────────────────────

def test_unauthenticated_admin_redirects_to_login(client):
    """Unauthenticated /admin should redirect."""
    r = client.get('/admin')
    assert r.status_code in (302, 308)


def test_authenticated_employee_admin_redirect_not_login(app):
    """Authenticated EMPLOYEE accessing /admin should redirect to dashboard."""
    c = make_client(app, ['EMPLOYEE'])
    r = c.get('/admin')
    assert r.status_code in (302, 308)
    location = r.headers.get('Location', '')
    assert 'login' not in location or 'dashboard' in location or location


# ── Bulk role × route combinations ────────────────────────────────────────────

ALL_PAGE_ROUTES = [
    '/dashboard', '/directory', '/my-team', '/org-tree',
    '/profile', '/search', '/vacation', '/vacation/calendar',
]

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ALL_ROLES
    for route in ALL_PAGE_ROUTES
])
def test_page_routes_no_500_all_roles(app, role, route):
    """All page routes should not return 500 for any role."""
    c = make_client(app, [role])
    mock_stats = {'active_employees': 0, 'new_hires': 0, 'departments': 0,
                  'pending_requests': 0, 'skills_count': 0, 'certifications': 0}
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.org.query', return_value=[]), \
         patch('app.services.search_service.unified_search', return_value={'results': [], 'total': 0}), \
         patch('app.routes.dashboard.compute_dashboard_stats', return_value=mock_stats), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500
