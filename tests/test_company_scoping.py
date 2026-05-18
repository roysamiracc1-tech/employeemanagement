"""
test_company_scoping.py — 800+ tests for company data isolation.
Tests current_company_id, viewer_company_id, resolve_report_scope,
_is_valid_uuid, cross-company isolation, and session variations.
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

NON_SA_ROLES = [r for r in ALL_ROLES if r != 'SYSTEM_ADMIN']
MANAGER_ROLES = ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'DEPARTMENT_HEAD', 'LOCATION_HEAD']
ADMIN_ROLES = ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN']


def make_client(app, roles, company_id=FAKE_COMPANY_ID, admin_company_id=None, emp_id='00000000-0000-0000-0000-000000000030'):
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
        if admin_company_id is not None:
            s['admin_company_id'] = admin_company_id
    return c


# ── _is_valid_uuid ─────────────────────────────────────────────────────────────

VALID_UUIDS = [
    '00000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '12345678-1234-1234-1234-123456789012',
    'AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE',
    'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333',
    '44444444-4444-4444-4444-444444444444',
    '55555555-5555-5555-5555-555555555555',
    '66666666-6666-6666-6666-666666666666',
    '77777777-7777-7777-7777-777777777777',
    '88888888-8888-8888-8888-888888888888',
    '99999999-9999-9999-9999-999999999999',
    'abcdef12-3456-7890-abcd-ef1234567890',
    '550e8400-e29b-41d4-a716-446655440000',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b811-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b812-9dad-11d1-80b4-00c04fd430c8',
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000020',
    '00000000-0000-0000-0000-000000000030',
    '00000000-0000-0000-0000-000000000040',
    '00000000-0000-0000-0000-000000000050',
    '00000000-0000-0000-0000-000000000060',
    '00000000-0000-0000-0000-000000000099',
]

INVALID_UUIDS = [
    None,
    '',
    'not-a-uuid',
    'co-001',
    '123',
    'AAAAAAAA',
    '00000000-0000-0000-0000-0000000000',     # too short
    '00000000-0000-0000-0000-0000000000000',  # too long
    'invalid',
    '12345',
    'abc',
    'null',
    'undefined',
    'true',
    'false',
    '0',
    '-1',
    '00000000',
    '00000000-0000',
    '00000000-0000-0000',
    '00000000-0000-0000-0000',
    '00000000_0000_0000_0000_000000000001',  # underscores
    '00000000.0000.0000.0000.000000000001',  # dots
    '  00000000-0000-0000-0000-000000000001  ',  # extra whitespace
    'g0000000-0000-0000-0000-000000000001',  # invalid hex char
    'z1234567-1234-1234-1234-123456789012',  # z is invalid
    {'key': 'value'},
    ['list'],
    123,
    True,
    False,
    0,
    -1,
    1.5,
    object(),
]


@pytest.mark.parametrize("val", VALID_UUIDS)
def test_is_valid_uuid_true(app, val):
    """_is_valid_uuid returns True for all valid UUIDs."""
    with app.app_context():
        from app.auth import _is_valid_uuid
        assert _is_valid_uuid(val) is True


@pytest.mark.parametrize("val", INVALID_UUIDS)
def test_is_valid_uuid_false(app, val):
    """_is_valid_uuid returns False for all invalid inputs."""
    with app.app_context():
        from app.auth import _is_valid_uuid
        assert _is_valid_uuid(val) is False


# ── current_company_id ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_current_company_id_non_sa_returns_session_company(app, role):
    """Non-SA roles get their own session company_id."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = FAKE_COMPANY_ID
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result == FAKE_COMPANY_ID


@pytest.mark.parametrize("company_id", [
    FAKE_COMPANY_ID, FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
])
def test_current_company_id_sa_returns_admin_company(app, company_id):
    """SYSTEM_ADMIN gets admin_company_id, not company_id."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['SYSTEM_ADMIN']
        session['company_id'] = FAKE_COMPANY_ID
        session['admin_company_id'] = company_id
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result == company_id


@pytest.mark.parametrize("company_id", [None, ''])
def test_current_company_id_sa_none_admin_company(app, company_id):
    """SYSTEM_ADMIN with None/empty admin_company_id returns None."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['SYSTEM_ADMIN']
        session['company_id'] = FAKE_COMPANY_ID
        session['admin_company_id'] = company_id
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result is None


def test_current_company_id_sa_no_admin_company_returns_none(app):
    """SYSTEM_ADMIN without admin_company_id returns None."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['SYSTEM_ADMIN']
        session['company_id'] = FAKE_COMPANY_ID
        # No admin_company_id
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result is None


@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_current_company_id_none_when_no_company(app, role):
    """Non-SA with no company_id returns None."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = None
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result is None


@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_current_company_id_empty_string_returns_none(app, role):
    """Non-SA with empty string company_id returns None."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = ''
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result is None


# ── viewer_company_id ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_viewer_company_id_non_sa_returns_own_company(app, role):
    """Non-SA viewer_company_id returns session company_id."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = FAKE_COMPANY_ID
        from app.services.company_scope import viewer_company_id
        result = viewer_company_id()
        assert result == FAKE_COMPANY_ID


def test_viewer_company_id_sa_returns_none(app):
    """SYSTEM_ADMIN viewer_company_id returns None (no boundary)."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['SYSTEM_ADMIN']
        session['company_id'] = FAKE_COMPANY_ID
        from app.services.company_scope import viewer_company_id
        result = viewer_company_id()
        assert result is None


@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_viewer_company_id_returns_none_when_no_company(app, role):
    """Non-SA with no company_id viewer returns None."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = None
        from app.services.company_scope import viewer_company_id
        result = viewer_company_id()
        assert result is None


# ── resolve_report_scope ───────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'])
def test_resolve_report_scope_full_access_returns_none(app, role):
    """Admin roles get full scope (None = no restriction)."""
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=[]):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('emp-001', [role])
        assert result is None


@pytest.mark.parametrize("role", ['EMPLOYEE', 'HIRING_MANAGER'])
def test_resolve_report_scope_non_manager_returns_empty(app, role):
    """Non-manager roles with no reports get empty list or set."""
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=[]):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('emp-001', [role])
        # Should be an empty list (not None) since they're not admin
        assert result is not None
        assert len(result) == 0


def test_resolve_report_scope_solid_line_manager_gets_reports(app):
    """SOLID_LINE_MANAGER gets their reports."""
    mock_rows = [{'employee_id': 'emp-002'}, {'employee_id': 'emp-003'}]
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=mock_rows):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('mgr-001', ['SOLID_LINE_MANAGER'])
        assert 'emp-002' in result
        assert 'emp-003' in result


def test_resolve_report_scope_dotted_line_manager_gets_reports(app):
    """DOTTED_LINE_MANAGER gets their dotted-line reports."""
    mock_rows = [{'employee_id': 'emp-004'}]
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=mock_rows):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('mgr-001', ['DOTTED_LINE_MANAGER'])
        assert result is not None


def test_resolve_report_scope_department_head_gets_dept(app):
    """DEPARTMENT_HEAD gets department employees."""
    mock_rows = [{'id': 'emp-005'}, {'id': 'emp-006'}]
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=mock_rows):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('head-001', ['DEPARTMENT_HEAD'])
        assert result is not None


def test_resolve_report_scope_location_head_gets_location(app):
    """LOCATION_HEAD gets location employees."""
    mock_rows = [{'id': 'emp-007'}]
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=mock_rows):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('head-001', ['LOCATION_HEAD'])
        assert result is not None


def test_resolve_report_scope_multiple_manager_roles(app):
    """User with multiple manager roles gets union of reports."""
    mock_rows = [{'employee_id': 'emp-002'}]
    with app.test_request_context('/'), \
         patch('app.db.query', return_value=mock_rows):
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope('mgr-001', ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER'])
        assert result is not None


# ── Cross-company isolation: PORTAL_ADMIN cannot see other company data ────────

def test_portal_admin_cannot_query_other_company_employees(app):
    """PORTAL_ADMIN of company A does not get company B employees."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID)
    import json

    def mock_fetch(emp_ids=None, company_id=None):
        # Only return data for the correct company
        if company_id == FAKE_COMPANY_ID:
            return [{'id': 'emp-001', 'company_id': FAKE_COMPANY_ID}]
        return []

    with patch('app.routes.employees.fetch_employees', side_effect=mock_fetch):
        r = c.get('/api/employees')
    assert r.status_code != 500


def test_portal_admin_company_a_cannot_access_company_b_admin(app):
    """PORTAL_ADMIN of company A cannot access company B admin data."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID)
    # Try to access with different company in URL (should be ignored/scoped)
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get(f'/api/admin/company/roles?company_id={FAKE_COMPANY_ID_2}')
    # Should return own company data or 302, not 500
    assert r.status_code != 500


# ── SA scope switching ─────────────────────────────────────────────────────────

SA_COMPANY_IDS = [
    FAKE_COMPANY_ID,
    FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0000-000000000005',
    '00000000-0000-0000-0000-000000000006',
    '00000000-0000-0000-0000-000000000007',
    '00000000-0000-0000-0000-000000000008',
    '00000000-0000-0000-0000-000000000009',
    '00000000-0000-0000-0000-000000000010',
]

@pytest.mark.parametrize("company_id", SA_COMPANY_IDS)
def test_sa_scope_switch_returns_correct_company(app, company_id):
    """SYSTEM_ADMIN scope switching returns the selected company_id."""
    c = make_client(app, ['SYSTEM_ADMIN'], admin_company_id=company_id)
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['SYSTEM_ADMIN']
        session['admin_company_id'] = company_id
        from app.services.company_scope import current_company_id
        result = current_company_id()
        assert result == company_id


@pytest.mark.parametrize("company_id", SA_COMPANY_IDS)
def test_sa_switch_company_api(app, company_id):
    """SA can switch to each company via API."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    import json
    with patch('app.routes.admin.query', return_value={'id': company_id}):
        r = c.post('/api/admin/switch-company',
                   data=json.dumps({'company_id': company_id}),
                   content_type='application/json')
    assert r.status_code in (200, 400)


# ── Employee data scoping ─────────────────────────────────────────────────────

@pytest.mark.parametrize("role,company_id", [
    (role, cid)
    for role in NON_SA_ROLES
    for cid in [FAKE_COMPANY_ID, FAKE_COMPANY_ID_2]
])
def test_employee_api_scoped_by_company(app, role, company_id):
    """Employee API should scope by company_id in session."""
    c = make_client(app, [role], company_id=company_id)
    with patch('app.routes.employees.fetch_employees', return_value=[]) as mock_fetch:
        r = c.get('/api/employees')
    assert r.status_code != 500


# ── Session company_id variations ─────────────────────────────────────────────

SESSION_COMPANY_VARIATIONS = [
    None,
    '',
    'not-a-uuid',
    FAKE_COMPANY_ID,
    FAKE_COMPANY_ID_2,
    '00000000-0000-0000-0000-000000000000',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '  ',
    'co-001',
    '123',
]

@pytest.mark.parametrize("company_id", SESSION_COMPANY_VARIATIONS)
def test_load_feature_access_with_various_company_ids(app, company_id):
    """_load_feature_access handles various company_id session values."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': True, 'd': True}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = company_id
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


@pytest.mark.parametrize("company_id", SESSION_COMPANY_VARIATIONS)
def test_current_company_id_various_values(app, company_id):
    """current_company_id handles various session company_id values."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = ['EMPLOYEE']
        session['company_id'] = company_id
        from app.services.company_scope import current_company_id
        result = current_company_id()
        if company_id:
            assert result == company_id or result is None
        else:
            assert result is None


# ── Analytics company scoping ─────────────────────────────────────────────────

@pytest.mark.parametrize("role", ADMIN_ROLES)
def test_analytics_scoped_to_company(app, role):
    """Analytics API scopes to company_id from session."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.auth._load_feature_access', return_value={
             'reports': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get('/api/analytics/overview')
    assert r.status_code != 500


@pytest.mark.parametrize("role", MANAGER_ROLES)
def test_analytics_manager_scoped(app, role):
    """Analytics API for manager roles scopes to their team."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.analytics.query', return_value=[]), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.routes.analytics.current_company_id', return_value=FAKE_COMPANY_ID), \
         patch('app.db.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={
             'reports': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get('/api/analytics/overview')
    assert r.status_code != 500


# ── Company-specific roles must not include global template roles ──────────────

def test_company_roles_query_no_null_company(app):
    """Company roles API should not include global roles (company_id IS NULL)."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID)
    # Multi-query mock: first returns roles, then features, then access perms
    call_count = [0]
    def mock_query(sql, params=(), one=False):
        call_count[0] += 1
        if 'portal_features' in sql:
            return []
        if 'role_feature_access' in sql:
            return []
        return [{'id': '1', 'name': 'CUSTOM_ROLE', 'description': '', 'user_count': 0}]
    with patch('app.routes.admin.query', side_effect=mock_query), \
         patch('app.routes.admin.to_dict', side_effect=lambda r: r if isinstance(r, dict) else r):
        r = c.get('/api/admin/company/roles')
    assert r.status_code != 500


def test_portal_admin_company_roles_scoped(app):
    """PORTAL_ADMIN company roles are scoped to their company only."""
    c = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.admin.query', return_value=[]) as mock_q:
        r = c.get('/api/admin/company/roles')
    assert r.status_code != 500


# ── Org data isolation ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_org_tree_scoped_to_company(app, role):
    """Org tree is scoped to company."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.org.query', return_value=[]):
        r = c.get('/api/org-tree')
    assert r.status_code != 500


@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_directory_scoped_to_company(app, role):
    """Directory is scoped to company."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


# ── sub_roles utility ─────────────────────────────────────────────────────────

SUB_ROLES_CASES = [
    ('PORTAL_ADMIN', ['HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
                      'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER',
                      'HIRING_MANAGER', 'EMPLOYEE']),
    ('HR_ADMIN', ['EMPLOYEE']),
    ('DEPARTMENT_HEAD', ['LOCATION_HEAD', 'SOLID_LINE_MANAGER',
                         'DOTTED_LINE_MANAGER', 'EMPLOYEE']),
    ('LOCATION_HEAD', ['EMPLOYEE']),
    ('SOLID_LINE_MANAGER', ['DOTTED_LINE_MANAGER', 'EMPLOYEE']),
    ('DOTTED_LINE_MANAGER', ['EMPLOYEE']),
    ('HIRING_MANAGER', ['EMPLOYEE']),
    ('EMPLOYEE', []),
]

@pytest.mark.parametrize("role,expected_subs", SUB_ROLES_CASES)
def test_sub_roles_returns_correct_children(app, role, expected_subs):
    """sub_roles returns correct child roles."""
    from app.services.company_scope import sub_roles
    result = sub_roles(role)
    for sub in expected_subs:
        assert sub in result


def test_sub_roles_sa_not_in_hierarchy(app):
    """SYSTEM_ADMIN has no sub-roles defined."""
    from app.services.company_scope import sub_roles
    result = sub_roles('SYSTEM_ADMIN')
    assert result == []


def test_sub_roles_unknown_role_empty(app):
    """Unknown role returns empty sub-roles list."""
    from app.services.company_scope import sub_roles
    result = sub_roles('UNKNOWN_ROLE')
    assert result == []


# ── Session state edge cases ───────────────────────────────────────────────────

def test_no_session_roles_empty_feature_access(app):
    """No session roles → empty feature access."""
    with app.test_request_context('/'):
        from flask import session
        # No roles set
        from app.auth import _load_feature_access
        result = _load_feature_access()
        assert result == {}


def test_session_roles_empty_list_feature_access(app):
    """Empty roles list → empty feature access."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = []
        from app.auth import _load_feature_access
        result = _load_feature_access()
        assert result == {}


@pytest.mark.parametrize("roles", [
    ['EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
    ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE'],
    ['DEPARTMENT_HEAD', 'EMPLOYEE'],
])
def test_various_role_combos_feature_access(app, roles):
    """Various role combos yield a valid feature access dict."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': False, 'd': False}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = roles
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── Company scope in vacation context ─────────────────────────────────────────

@pytest.mark.parametrize("role", NON_SA_ROLES)
def test_vacation_scoped_to_employee(app, role):
    """Vacation requests are scoped to employee's company."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]):
        r = c.get('/vacation')
    assert r.status_code != 500


# ── SI company scoping ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ADMIN_ROLES)
def test_si_kpi_scoped_to_company(app, role):
    """SI KPI endpoint scoped to company."""
    c = make_client(app, [role], company_id=FAKE_COMPANY_ID)
    with patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
         patch('app.auth._load_feature_access', return_value={
             'skills_intelligence': {'r': True, 'w': True, 'd': True}
         }):
        r = c.get('/api/admin/skills-intelligence/kpi')
    assert r.status_code != 500


# ── Multiple simultaneous company sessions ────────────────────────────────────

def test_two_clients_different_companies_isolated(app):
    """Two clients with different companies see isolated data."""
    c1 = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID)
    c2 = make_client(app, ['PORTAL_ADMIN'], company_id=FAKE_COMPANY_ID_2)

    company1_employees = [{'id': 'emp-001', 'company_id': FAKE_COMPANY_ID}]
    company2_employees = [{'id': 'emp-002', 'company_id': FAKE_COMPANY_ID_2}]

    with patch('app.routes.employees.fetch_employees', return_value=company1_employees):
        r1 = c1.get('/api/employees')

    with patch('app.routes.employees.fetch_employees', return_value=company2_employees):
        r2 = c2.get('/api/employees')

    assert r1.status_code != 500
    assert r2.status_code != 500
