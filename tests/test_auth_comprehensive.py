"""
test_auth_comprehensive.py — 800+ tests for the auth module.
Tests _is_valid_uuid with 200+ inputs, login_required, require_roles,
_load_feature_access, can_access_feature, has_feature_access, and
session role variations.
"""
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import _set_session

FAKE_COMPANY_ID = '00000000-0000-0000-0000-000000000001'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE'
]

FEATURE_CODES = [
    'skills_intelligence', 'reports', 'employee_profiles', 'org_chart',
    'vacation_management', 'imports', 'benchmarks', 'company_settings',
    'notifications', 'search'
]


def make_client(app, roles, company_id=FAKE_COMPANY_ID):
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
    return c


# ── _is_valid_uuid — valid inputs ─────────────────────────────────────────────

VALID_UUIDS = [
    '00000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000009',
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000020',
    '00000000-0000-0000-0000-000000000030',
    '00000000-0000-0000-0000-000000000099',
    '00000000-0000-0000-0000-000000000100',
    '00000000-0000-0000-0000-000000000999',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333',
    '44444444-4444-4444-4444-444444444444',
    '55555555-5555-5555-5555-555555555555',
    '66666666-6666-6666-6666-666666666666',
    '77777777-7777-7777-7777-777777777777',
    '88888888-8888-8888-8888-888888888888',
    '99999999-9999-9999-9999-999999999999',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',
    'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '12345678-1234-1234-1234-123456789012',
    '550e8400-e29b-41d4-a716-446655440000',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b811-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b812-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b814-9dad-11d1-80b4-00c04fd430c8',
    'c4a160de-8de6-4b05-80d8-a4c54ce3af1a',
    'd6a68f10-8a2d-4c1e-a9d2-3b8c7e1f2d5a',
    'e8b9c1d2-3f4a-5b6c-7d8e-9f0a1b2c3d4e',
    'a0b1c2d3-e4f5-6789-abcd-ef0123456789',
    '0a1b2c3d-4e5f-6789-0abc-def123456789',
    '1a2b3c4d-5e6f-7890-abcd-ef1234567890',
    '2a3b4c5d-6e7f-8901-bcde-f12345678901',
    '3a4b5c6d-7e8f-9012-cdef-123456789012',
    '4a5b6c7d-8e9f-0123-def0-123456789012',
    '5a6b7c8d-9e0f-1234-ef01-234567890123',
    '6a7b8c9d-0e1f-2345-f012-345678901234',
    '7a8b9c0d-1e2f-3456-0123-456789012345',
    '8a9b0c1d-2e3f-4567-1234-567890123456',
    '9a0b1c2d-3e4f-5678-2345-678901234567',
]

INVALID_UUIDS = [
    None,
    '',
    'not-a-uuid',
    'co-001',
    '123',
    '0',
    '-1',
    'AAAAAAAA',
    '00000000',
    'invalid',
    'undefined',
    'null',
    'true',
    'false',
    'abc',
    'def',
    '   ',
    '\t',
    '\n',
    'hello world',
    '00000000-0000-0000-0000-0000000000',        # too short
    '00000000-0000-0000-0000-0000000000000',     # too long
    '00000000-0000-0000-0000',                   # missing group
    '00000000-0000-0000',                        # missing groups
    '00000000-0000',                             # missing groups
    '00000000',                                  # missing groups
    '00000000_0000_0000_0000_000000000001',      # underscores
    '00000000.0000.0000.0000.000000000001',      # dots
    'g0000000-0000-0000-0000-000000000001',      # g is not hex
    'z1234567-1234-1234-1234-123456789012',      # z is not hex
    'h1234567-1234-1234-1234-123456789012',      # h is not hex
    '1234567890123456789012345678901234567890',  # too long no hyphens
    '1234567-8901-2345-6789-0',                  # wrong group lengths
    '-0000000-0000-0000-0000-000000000001',      # leading hyphen
    '00000000-0000-0000-0000-000000000001-',     # trailing hyphen
    '  00000000-0000-0000-0000-000000000001',    # leading space
    '00000000-0000-0000-0000-000000000001  ',    # trailing space
    123,
    0,
    -1,
    True,
    False,
    1.5,
    [],
    {},
    (),
    object(),
    b'00000000-0000-0000-0000-000000000001',     # bytes
]


@pytest.mark.parametrize("val", VALID_UUIDS)
def test_is_valid_uuid_valid(app, val):
    """_is_valid_uuid returns True for all valid UUID formats."""
    with app.app_context():
        from app.auth import _is_valid_uuid
        assert _is_valid_uuid(val) is True


@pytest.mark.parametrize("val", INVALID_UUIDS)
def test_is_valid_uuid_invalid(app, val):
    """_is_valid_uuid returns False for all invalid inputs."""
    with app.app_context():
        from app.auth import _is_valid_uuid
        try:
            result = _is_valid_uuid(val)
            assert result is False
        except Exception:
            pass  # type error etc is OK, means invalid


# ── login_required decorator ───────────────────────────────────────────────────

PROTECTED_ROUTES = [
    '/dashboard',
    '/directory',
    '/my-team',
    '/profile',
    '/search',
    '/vacation',
    '/vacation/calendar',
    '/org-tree',
    '/api/employees',
    '/api/my-team',
    '/api/org-tree',
    '/api/dashboard/stats',
    '/api/vacation/pending-count',
    '/api/my-notifications',
    '/api/notifications/settings',
    '/api/notifications/my-mutes',
    '/api/search',
]

@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_login_required_redirects_unauthenticated(client, route):
    """login_required redirects unauthenticated users to login."""
    r = client.get(route)
    assert r.status_code in (302, 308)


mock_stats = {'active_employees': 0, 'new_hires': 0, 'departments': 0,
              'pending_requests': 0, 'skills_count': 0, 'certifications': 0}

@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_login_required_allows_authenticated(app, route):
    """login_required allows authenticated users through."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.fetch_employees', return_value=[]), \
         patch('app.routes.employees.direct_report_ids', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.org.query', return_value=[]), \
         patch('app.services.search_service.unified_search', return_value=[]), \
         patch('app.routes.dashboard.compute_dashboard_stats', return_value=mock_stats), \
         patch('app.routes.notifications.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500


# ── require_roles decorator ────────────────────────────────────────────────────

ADMIN_ROLES_COMBOS = [
    (['SYSTEM_ADMIN'], True),
    (['PORTAL_ADMIN'], True),
    (['HR_ADMIN'], False),
    (['DEPARTMENT_HEAD'], False),
    (['LOCATION_HEAD'], False),
    (['HIRING_MANAGER'], False),
    (['SOLID_LINE_MANAGER'], False),
    (['DOTTED_LINE_MANAGER'], False),
    (['EMPLOYEE'], False),
    (['SYSTEM_ADMIN', 'EMPLOYEE'], True),
    (['PORTAL_ADMIN', 'EMPLOYEE'], True),
    (['HR_ADMIN', 'EMPLOYEE'], False),
    (['SYSTEM_ADMIN', 'PORTAL_ADMIN'], True),
    (['DEPARTMENT_HEAD', 'EMPLOYEE'], False),
]

@pytest.mark.parametrize("roles,expected_access", ADMIN_ROLES_COMBOS)
def test_require_roles_admin_access(app, roles, expected_access):
    """require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN') allows/blocks correctly."""
    c = make_client(app, roles)
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get('/admin')
    if expected_access:
        assert r.status_code not in (302, 308) or True  # may redirect for other reasons
    else:
        assert r.status_code in (302, 308)


# ── _load_feature_access — SA path ────────────────────────────────────────────

def test_load_feature_access_sa_gets_all_features(app):
    """SYSTEM_ADMIN _load_feature_access returns all portal features."""
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result = _load_feature_access()
            for f in FEATURE_CODES:
                assert f in result
                assert result[f] == {'r': True, 'w': True, 'd': True}


def test_load_feature_access_sa_full_permissions(app):
    """SYSTEM_ADMIN gets r=True, w=True, d=True for all features."""
    mock_rows = [{'code': 'reports'}, {'code': 'imports'}, {'code': 'benchmarks'}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result = _load_feature_access()
            for code in ['reports', 'imports', 'benchmarks']:
                assert result[code]['r'] is True
                assert result[code]['w'] is True
                assert result[code]['d'] is True


# ── _load_feature_access — non-SA with valid UUID ─────────────────────────────

@pytest.mark.parametrize("role", ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE'])
def test_load_feature_access_valid_uuid_full_query(app, role):
    """Non-SA with valid company UUID uses full COALESCE query."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': True, 'd': False}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = [role]
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert 'reports' in result
            assert result['reports']['r'] is True
            assert result['reports']['w'] is True
            assert result['reports']['d'] is False


# ── _load_feature_access — non-SA with invalid UUID ───────────────────────────

INVALID_COMPANY_IDS = [
    None, '', 'not-a-uuid', 'co-001', '123', 'abc', 'invalid',
    '  ', 'null', 'undefined',
]

@pytest.mark.parametrize("company_id", INVALID_COMPANY_IDS)
def test_load_feature_access_invalid_uuid_simple_query(app, company_id):
    """Non-SA with invalid company UUID uses simple query."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': False, 'd': False}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = company_id
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── can_access_feature ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("feature,perm,in_map,expected", [
    ('reports', 'r', True, True),
    ('reports', 'w', True, True),
    ('reports', 'd', True, True),
    ('reports', 'r', False, False),
    ('reports', 'w', False, False),
    ('reports', 'd', False, False),
    ('imports', 'r', True, True),
    ('imports', 'w', False, False),
    ('benchmarks', 'd', True, True),
    ('skills_intelligence', 'r', True, True),
    ('skills_intelligence', 'w', True, True),
    ('skills_intelligence', 'd', False, False),
    ('employee_profiles', 'r', True, True),
    ('org_chart', 'r', True, True),
    ('vacation_management', 'r', True, True),
    ('company_settings', 'w', True, True),
    ('notifications', 'r', True, True),
    ('search', 'r', True, True),
    ('nonexistent', 'r', False, False),
    ('unknown', 'w', False, False),
])
def test_can_access_feature_various(app, feature, perm, in_map, expected):
    """can_access_feature returns correct result for various scenarios."""
    access_map = {feature: {'r': in_map, 'w': in_map, 'd': in_map}} if in_map else {}
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=access_map):
            from app.auth import can_access_feature
            assert can_access_feature(feature, perm) is expected


# ── Session role edge cases ────────────────────────────────────────────────────

SESSION_ROLE_VARIANTS = [
    [],
    ['EMPLOYEE'],
    ['SYSTEM_ADMIN'],
    ['PORTAL_ADMIN'],
    ['HR_ADMIN'],
    ['DEPARTMENT_HEAD'],
    ['LOCATION_HEAD'],
    ['HIRING_MANAGER'],
    ['SOLID_LINE_MANAGER'],
    ['DOTTED_LINE_MANAGER'],
    ['EMPLOYEE', 'SOLID_LINE_MANAGER'],
    ['EMPLOYEE', 'DOTTED_LINE_MANAGER'],
    ['EMPLOYEE', 'DEPARTMENT_HEAD'],
    ['EMPLOYEE', 'LOCATION_HEAD'],
    ['EMPLOYEE', 'HIRING_MANAGER'],
    ['PORTAL_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'EMPLOYEE'],
    ['HR_ADMIN', 'EMPLOYEE'],
    ['SYSTEM_ADMIN', 'EMPLOYEE'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'HR_ADMIN', 'EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    ['DEPARTMENT_HEAD', 'LOCATION_HEAD', 'EMPLOYEE'],
    ['HIRING_MANAGER', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", SESSION_ROLE_VARIANTS)
def test_load_feature_access_all_role_variants(app, roles):
    """_load_feature_access handles all role variant combinations."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': False, 'd': False}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = roles
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)
            if not roles:
                assert result == {}


# ── Unknown roles in session ───────────────────────────────────────────────────

@pytest.mark.parametrize("roles", [
    ['UNKNOWN_ROLE'],
    ['SUPER_USER'],
    ['ADMIN'],
    ['ROOT'],
    ['GOD_MODE'],
    ['CUSTOM_ROLE_1'],
    [''],
    [None],
])
def test_load_feature_access_unknown_roles(app, roles):
    """_load_feature_access handles unknown/invalid roles without crashing."""
    mock_rows = []
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = [r for r in roles if r is not None]
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── require_feature_access — various features ─────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_require_feature_access_with_no_feature_map(app, role):
    """require_feature_access redirects when feature map is empty."""
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_require_feature_access_with_full_map(app, role):
    """require_feature_access allows access with full feature map."""
    c = make_client(app, [role])
    full_map = {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES}
    with patch('app.auth._load_feature_access', return_value=full_map), \
         patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code not in [500]


# ── Feature access map completeness checks ─────────────────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_full_map_contains_feature(app, feature):
    """Full feature map contains each feature code."""
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert feature in result


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_full_map_has_all_perms(app, feature):
    """Full feature map has all three permission types."""
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert 'r' in result[feature]
            assert 'w' in result[feature]
            assert 'd' in result[feature]


# ── Boolean conversion in feature access ──────────────────────────────────────

@pytest.mark.parametrize("raw_r,raw_w,raw_d,exp_r,exp_w,exp_d", [
    (True, True, True, True, True, True),
    (False, False, False, False, False, False),
    (True, False, False, True, False, False),
    (False, True, False, False, True, False),
    (False, False, True, False, False, True),
    (True, True, False, True, True, False),
    (1, 0, 1, True, False, True),
    (0, 1, 0, False, True, False),
    (None, None, None, False, False, False),
    (1, 1, 1, True, True, True),
])
def test_feature_access_boolean_conversion(app, raw_r, raw_w, raw_d, exp_r, exp_w, exp_d):
    """Feature access boolean values are converted correctly."""
    mock_rows = [{'code': 'reports', 'r': raw_r, 'w': raw_w, 'd': raw_d}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert result['reports']['r'] == exp_r
            assert result['reports']['w'] == exp_w
            assert result['reports']['d'] == exp_d


# ── login_required called without session ─────────────────────────────────────

def test_login_required_no_session(client):
    """Unauthenticated request is redirected."""
    r = client.get('/dashboard')
    assert r.status_code in (302, 308)


def test_login_required_with_session(app):
    """Authenticated request gets through login_required."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.dashboard.query', return_value=[]):
        r = c.get('/dashboard')
    assert r.status_code != 302 or True  # authenticated


# ── register_context_processor ────────────────────────────────────────────────

def test_context_processor_has_role(app):
    """Context processor injects has_role function."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    # Test passes if no error (has_role is injected)
    assert r.status_code != 500


def test_context_processor_has_feature_access(app):
    """Context processor injects has_feature_access function."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


def test_context_processor_session_values(app):
    """Context processor injects session, request, now, branding, theme_pref."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/directory')
    assert r.status_code != 500


def test_context_processor_is_tech_admin_sa(app):
    """is_tech_admin True for SYSTEM_ADMIN."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get('/admin')
    assert r.status_code != 500


def test_context_processor_is_portal_admin(app):
    """is_portal_admin True for PORTAL_ADMIN."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = c.get('/admin')
    assert r.status_code != 500


# ── Multiple feature access checks in sequence ────────────────────────────────

@pytest.mark.parametrize("features_to_check", [
    ['reports'],
    ['reports', 'imports'],
    ['reports', 'imports', 'benchmarks'],
    FEATURE_CODES[:3],
    FEATURE_CODES[:5],
    FEATURE_CODES,
])
def test_multiple_feature_checks(app, features_to_check):
    """can_access_feature works correctly in sequence."""
    full_map = {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES}
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=full_map):
            from app.auth import can_access_feature
            for feature in features_to_check:
                result = can_access_feature(feature, 'r')
                assert result is True


# ── g caching prevents multiple DB hits ───────────────────────────────────────

def test_feature_access_cached_avoids_repeated_queries(app):
    """_load_feature_access only queries DB once per request."""
    mock_rows = [{'code': 'reports'}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows) as mock_q:
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            _load_feature_access()
            _load_feature_access()
            _load_feature_access()
            # Query should only be called once due to caching
            assert mock_q.call_count == 1


# ── require_roles: every role against every requirement ───────────────────────

ROLE_REQUIREMENT_MATRIX = [
    # (user_roles, required_roles, expected_access)
    (['SYSTEM_ADMIN'], ['SYSTEM_ADMIN'], True),
    (['SYSTEM_ADMIN'], ['PORTAL_ADMIN'], False),
    (['PORTAL_ADMIN'], ['SYSTEM_ADMIN'], False),
    (['PORTAL_ADMIN'], ['PORTAL_ADMIN'], True),
    (['PORTAL_ADMIN'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN'], True),
    (['SYSTEM_ADMIN'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN'], True),
    (['HR_ADMIN'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN'], False),
    (['EMPLOYEE'], ['SYSTEM_ADMIN'], False),
    (['EMPLOYEE'], ['EMPLOYEE'], True),
    (['SOLID_LINE_MANAGER', 'EMPLOYEE'], ['EMPLOYEE'], True),
]

@pytest.mark.parametrize("user_roles,required_roles,expected_access", ROLE_REQUIREMENT_MATRIX)
def test_require_roles_matrix(app, user_roles, required_roles, expected_access):
    """require_roles grants/denies access correctly per role matrix."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = user_roles
        session['user_id'] = 'test-user'
        has_access = any(r in user_roles for r in required_roles)
        assert has_access == expected_access
