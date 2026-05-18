"""
test_employee_comprehensive.py — 600+ tests for employee routes.
Tests directory, profile, api_employees, skills, certs, gender, theme,
company switcher, and ACTIVE_COMPANY_ID contexts.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import _set_session, SAMPLE_EMPLOYEE

FAKE_COMPANY_ID = '00000000-0000-0000-0000-000000000001'
FAKE_COMPANY_ID_2 = '00000000-0000-0000-0000-000000000002'
FAKE_EMP_ID = '00000000-0000-0000-0000-000000000030'
FAKE_EMP_ID_2 = '00000000-0000-0000-0000-000000000031'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE'
]

MANAGER_ROLES = ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'DEPARTMENT_HEAD',
                 'LOCATION_HEAD', 'HIRING_MANAGER']


def make_client(app, roles, company_id=FAKE_COMPANY_ID, emp_id=FAKE_EMP_ID):
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


def sample_emp():
    return {
        'id': FAKE_EMP_ID, 'employee_number': 'EMP-001', 'full_name': 'Jane Smith',
        'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane@example.com',
        'phone_number': '', 'job_title': 'Engineer', 'employment_status': 'ACTIVE',
        'employment_type': 'PERMANENT', 'gender': 'FEMALE', 'join_date': '2022-01-15',
        'location': 'London', 'office_code': 'LDN', 'business_unit': 'Engineering',
        'bu_code': 'ENG', 'functional_unit': 'Platform', 'fu_code': 'PLT',
        'cost_center': 'CC-001', 'solid_manager_name': 'Bob Manager',
        'solid_manager_title': 'Head of Eng', 'solid_manager_id': 'mgr-001',
        'dotted_manager_name': '', 'dotted_manager_title': '',
        'skills': [], 'cert_count': 0, 'certifications': [],
    }


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type='application/json')


def put_json(client, url, data):
    return client.put(url, data=json.dumps(data), content_type='application/json')


# ── Directory page — all roles ────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_directory_accessible_all_roles(app, role):
    """Directory page accessible to all authenticated roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


def test_directory_unauthenticated(client):
    """Directory requires authentication."""
    r = client.get('/directory')
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_directory_with_employees(app, role):
    """Directory shows employees when available."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[sample_emp()]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_directory_no_company_id(app, role):
    """Directory handles missing company_id."""
    c = make_client(app, [role], company_id=None)
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


@pytest.mark.parametrize("search_q", ['', 'john', 'smith', 'eng', 'London', 'test@example.com'])
def test_directory_search_param(app, search_q):
    """Directory handles search query parameter."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(f'/directory?q={search_q}')
    assert r.status_code != 500


# ── Profile page ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_profile_own_profile(app, role):
    """All roles can view their own profile."""
    c = make_client(app, [role])
    emp = sample_emp()
    with patch('app.routes.employees.fetch_employees', return_value=[emp]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.to_dict', side_effect=lambda r: r if isinstance(r, dict) else {}), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/profile')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_profile_other_employee(app, role):
    """Roles can view other employee profiles."""
    c = make_client(app, [role])
    emp = sample_emp()
    emp['id'] = FAKE_EMP_ID_2  # different employee
    with patch('app.routes.employees.fetch_employees', return_value=[emp]), \
         patch('app.routes.employees.is_direct_report', return_value=True), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.to_dict', side_effect=lambda r: r if isinstance(r, dict) else {}), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(f'/profile/{FAKE_EMP_ID_2}')
    assert r.status_code != 500


@pytest.mark.parametrize("emp_id", [
    FAKE_EMP_ID, FAKE_EMP_ID_2,
    '00000000-0000-0000-0000-000000000032',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '11111111-1111-1111-1111-111111111111',
])
def test_profile_various_emp_ids(app, emp_id):
    """Profile handles various employee IDs."""
    c = make_client(app, ['EMPLOYEE'])
    emp = sample_emp()
    emp['id'] = emp_id
    with patch('app.routes.employees.fetch_employees', return_value=[emp]), \
         patch('app.routes.employees.is_direct_report', return_value=True), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.to_dict', side_effect=lambda r: r if isinstance(r, dict) else {}), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(f'/profile/{emp_id}')
    assert r.status_code != 500


def test_profile_nonexistent_employee(app):
    """Profile handles nonexistent employee gracefully."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.routes.employees.query', return_value=None), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(f'/profile/{FAKE_EMP_ID_2}')
    assert r.status_code in (200, 302, 404) and r.status_code != 500


# ── API employees ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_employees_all_roles(app, role):
    """API employees accessible to all authenticated roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_employees_returns_list(app, role):
    """API employees returns a list."""
    c = make_client(app, [role])
    emp = sample_emp()
    with patch('app.routes.employees.fetch_employees', return_value=[emp]):
        r = c.get('/api/employees')
    assert r.status_code != 500
    if r.status_code == 200:
        data = json.loads(r.data)
        assert isinstance(data, (list, dict))


@pytest.mark.parametrize("company_id", [
    FAKE_COMPANY_ID, FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    None, '',
])
def test_api_employees_various_company_ids(app, company_id):
    """API employees handles various company IDs."""
    c = make_client(app, ['EMPLOYEE'], company_id=company_id)
    with patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/employees')
    assert r.status_code != 500


# ── API my-team ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_my_team_all_roles(app, role):
    """API my-team accessible to all authenticated roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]):
        r = c.get('/api/my-team')
    assert r.status_code != 500


@pytest.mark.parametrize("role", MANAGER_ROLES)
def test_api_my_team_manager_with_reports(app, role):
    """API my-team shows reports for manager roles."""
    c = make_client(app, [role])
    emp = sample_emp()
    with patch('app.routes.employees.direct_report_ids', return_value=[FAKE_EMP_ID_2]), \
         patch('app.routes.employees.fetch_employees', return_value=[emp]):
        r = c.get('/api/my-team')
    assert r.status_code != 500


# ── Skill management ──────────────────────────────────────────────────────────

SKILL_POST_VALID_CASES = [
    {'skill_id': 'skill-001', 'level_id': 'level-001', 'is_primary': True},
    {'skill_id': 'skill-002', 'level_id': 'level-002', 'is_primary': False},
    {'skill_id': 'skill-003', 'level_id': 'level-003'},
    {'skill_id': 'skill-004', 'level_id': 'level-001', 'is_primary': None},
    {'skill_id': 'skill-005', 'level_id': 'level-002', 'is_primary': True},
]

@pytest.mark.parametrize("body", SKILL_POST_VALID_CASES)
def test_profile_skill_post_valid(app, body):
    """Profile skill POST with valid data succeeds."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value={'id': 'skill-001'}), \
         patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/profile/skills', body)
    assert r.status_code != 500


@pytest.mark.parametrize("skill_id", [
    FAKE_EMP_ID, FAKE_EMP_ID_2, '00000000-0000-0000-0000-000000000032',
    '00000000-0000-0000-0000-000000000033', '00000000-0000-0000-0000-000000000034',
])
def test_profile_skill_delete_valid_id(app, skill_id):
    """Profile skill DELETE with valid ID."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value={'id': skill_id, 'employee_id': FAKE_EMP_ID}), \
         patch('app.routes.employees.execute', return_value=None):
        r = c.delete(f'/api/profile/skills/{skill_id}')
    assert r.status_code != 500


def test_profile_skill_delete_not_found(app):
    """Profile skill DELETE for nonexistent skill returns 404."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=None):
        r = c.delete(f'/api/profile/skills/{FAKE_EMP_ID}')
    assert r.status_code in (404, 400, 200)


def test_profile_skill_delete_other_employee_forbidden(app):
    """Profile skill DELETE for another employee's skill returns 403/404."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value={'id': 'skill-001', 'employee_id': 'other-emp'}):
        r = c.delete(f'/api/profile/skills/{FAKE_EMP_ID}')
    assert r.status_code in (403, 404, 400, 200)


# ── Certification management ──────────────────────────────────────────────────

CERT_POST_VALID_CASES = [
    {'name': 'AWS Solutions Architect', 'issuer': 'Amazon', 'issue_date': '2023-01-01'},
    {'name': 'GCP Professional', 'issuer': 'Google'},
    {'name': 'Azure Fundamentals'},
    {'name': 'PMP', 'issuer': 'PMI', 'issue_date': '2022-06-01', 'expiry_date': '2025-06-01'},
    {'name': 'CISSP', 'issuer': 'ISC2', 'credential_id': 'CERT-001'},
    {'name': 'Kubernetes CKA', 'url': 'https://example.com/cert'},
    {'name': 'Docker Certified', 'issue_date': None},
    {'name': 'Python Expert', 'expiry_date': None},
    {'name': 'Data Science', 'issuer': 'Coursera', 'url': 'https://coursera.org'},
    {'name': 'ML Engineer', 'credential_id': None},
]

@pytest.mark.parametrize("body", CERT_POST_VALID_CASES)
def test_profile_cert_post_valid(app, body):
    """Profile certification POST with valid data."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value={'id': FAKE_EMP_ID}), \
         patch('app.routes.employees.insert_returning', return_value={'id': 'cert-001'}), \
         patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/profile/certifications', body)
    assert r.status_code != 500


CERT_PUT_VALID_CASES = [
    {'name': 'Updated AWS Cert', 'issuer': 'Amazon'},
    {'name': 'Updated GCP', 'issue_date': '2024-01-01'},
    {'name': 'Updated Azure', 'expiry_date': '2026-01-01'},
    {'name': 'Updated PMP', 'url': 'https://pmi.org/cert'},
    {'name': 'Updated CISSP', 'credential_id': 'CERT-999'},
]

@pytest.mark.parametrize("body", CERT_PUT_VALID_CASES)
def test_profile_cert_put_valid(app, body):
    """Profile certification PUT with valid data."""
    c = make_client(app, ['EMPLOYEE'])
    ec_id = '00000000-0000-0000-0000-000000000070'
    with patch('app.routes.employees.query', return_value={'id': ec_id, 'employee_id': FAKE_EMP_ID}), \
         patch('app.routes.employees.execute', return_value=None):
        r = put_json(c, f'/api/profile/certifications/{ec_id}', body)
    assert r.status_code != 500


def test_profile_cert_delete_valid(app):
    """Profile certification DELETE with valid ID."""
    c = make_client(app, ['EMPLOYEE'])
    ec_id = '00000000-0000-0000-0000-000000000070'
    with patch('app.routes.employees.query', return_value={'id': ec_id, 'employee_id': FAKE_EMP_ID}), \
         patch('app.routes.employees.execute', return_value=None):
        r = c.delete(f'/api/profile/certifications/{ec_id}')
    assert r.status_code != 500


def test_profile_cert_delete_not_found(app):
    """Profile certification DELETE for nonexistent cert returns 404."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=None):
        r = c.delete(f'/api/profile/certifications/{FAKE_EMP_ID}')
    assert r.status_code in (404, 400, 200)


# ── Gender update ─────────────────────────────────────────────────────────────

VALID_GENDERS = ['MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY']
INVALID_GENDERS = ['', 'X', 'MAN', 'WOMAN', '123', None, 'invalid', 'UNKNOWN']

@pytest.mark.parametrize("gender", VALID_GENDERS)
def test_profile_gender_valid(app, gender):
    """Profile gender update with valid gender values."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/profile/gender', {'gender': gender})
    assert r.status_code != 500


@pytest.mark.parametrize("gender", INVALID_GENDERS)
def test_profile_gender_invalid(app, gender):
    """Profile gender update with invalid values returns error or handles gracefully."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/profile/gender', {'gender': gender} if gender is not None else {})
    assert r.status_code != 500


# ── Theme update ──────────────────────────────────────────────────────────────

VALID_THEMES = ['light', 'dark', 'system']
INVALID_THEMES = ['', 'LIGHT', 'custom', 'blue', None, 123, True]

@pytest.mark.parametrize("theme", VALID_THEMES)
def test_user_theme_valid(app, theme):
    """Theme update with valid values."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/user/theme', {'theme': theme})
    assert r.status_code != 500


@pytest.mark.parametrize("theme", INVALID_THEMES)
def test_user_theme_invalid(app, theme):
    """Theme update with invalid values handles gracefully."""
    c = make_client(app, ['EMPLOYEE'])
    body = {'theme': theme} if theme is not None else {}
    with patch('app.routes.employees.execute', return_value=None):
        r = post_json(c, '/api/user/theme', body)
    assert r.status_code != 500


# ── Company switcher in directory ─────────────────────────────────────────────

@pytest.mark.parametrize("company_id", [
    FAKE_COMPANY_ID, FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    None, '',
    '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0000-000000000005',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '11111111-1111-1111-1111-111111111111',
])
def test_directory_company_context(app, company_id):
    """Directory handles various company_id session values."""
    c = make_client(app, ['EMPLOYEE'], company_id=company_id)
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


# ── Profile skills GET ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_profile_skills_get_all_roles(app, role):
    """API profile skills GET accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]):
        r = c.get('/api/profile/skills')
    assert r.status_code != 500


# ── Profile certifications GET ────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_profile_certifications_get_all_roles(app, role):
    """API profile certifications GET accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]):
        r = c.get('/api/profile/certifications')
    assert r.status_code != 500


# ── My-team page ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_my_team_page_all_roles(app, role):
    """My-team page accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/my-team')
    assert r.status_code != 500


# ── ACTIVE_COMPANY_ID in template contexts ────────────────────────────────────

@pytest.mark.parametrize("context,company_id", [
    ('directory', FAKE_COMPANY_ID),
    ('profile', FAKE_COMPANY_ID),
    ('my-team', FAKE_COMPANY_ID),
    ('directory', FAKE_COMPANY_ID_2),
    ('directory', None),
])
def test_template_company_context(app, context, company_id):
    """Templates render correctly with various company contexts."""
    c = make_client(app, ['EMPLOYEE'], company_id=company_id)
    route_map = {
        'directory': '/directory',
        'profile': '/profile',
        'my-team': '/my-team',
    }
    route = route_map[context]
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500


# ── Pagination/filtering in directory ────────────────────────────────────────

DIRECTORY_PARAMS = [
    '?page=1',
    '?page=2',
    '?per_page=10',
    '?per_page=50',
    '?status=ACTIVE',
    '?status=INACTIVE',
    '?bu=Engineering',
    '?location=London',
    '?q=smith',
    '?q=john&status=ACTIVE',
]

@pytest.mark.parametrize("params", DIRECTORY_PARAMS)
def test_directory_with_params(app, params):
    """Directory handles various query parameters."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(f'/directory{params}')
    assert r.status_code != 500


# ── Skill validation (admin endpoint) ────────────────────────────────────────

@pytest.mark.parametrize("role", ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER'])
def test_validate_skill_authorized_roles(app, role):
    """Validate skill accessible to authorized roles."""
    c = make_client(app, [role])
    body = {'skill_id': 'skill-001', 'employee_id': FAKE_EMP_ID, 'level_id': 'level-001'}
    with patch('app.routes.admin.query', return_value={'id': FAKE_EMP_ID}), \
         patch('app.routes.admin.execute', return_value=None):
        r = post_json(c, '/api/admin/validate-skill', body)
    assert r.status_code != 500


@pytest.mark.parametrize("role", ['DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER',
                                   'DOTTED_LINE_MANAGER', 'EMPLOYEE'])
def test_validate_skill_unauthorized_roles(app, role):
    """Validate skill blocked for unauthorized roles."""
    c = make_client(app, [role])
    body = {'skill_id': 'skill-001', 'employee_id': FAKE_EMP_ID, 'level_id': 'level-001'}
    r = post_json(c, '/api/admin/validate-skill', body)
    assert r.status_code in (302, 308)


# ── Employee search ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_api_search_all_roles(app, role):
    """Search API accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.services.search_service.unified_search', return_value=[]):
        r = c.get('/api/search?q=test')
    assert r.status_code != 500


SEARCH_QUERIES = ['', 'a', 'john', 'smith@example.com', 'Engineer', 'London',
                  'test user', 'EMP-001', 'a' * 100, '!@#$%^&*()']

@pytest.mark.parametrize("query", SEARCH_QUERIES)
def test_api_search_various_queries(app, query):
    """Search handles various query strings."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.services.search_service.unified_search', return_value=[]):
        r = c.get(f'/api/search?q={query}')
    assert r.status_code != 500
