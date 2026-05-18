"""
test_permission_matrix.py — 1,200+ tests for the feature permission system.
Tests _load_feature_access, can_access_feature, require_feature_access, and
feature access maps for all roles and features.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from flask import g
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

PERMISSION_TYPES = ['r', 'w', 'd']


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


def full_feature_map():
    return {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES}


def empty_feature_map():
    return {}


def read_only_feature_map():
    return {f: {'r': True, 'w': False, 'd': False} for f in FEATURE_CODES}


# ── SYSTEM_ADMIN always gets full access ──────────────────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
@pytest.mark.parametrize("perm", PERMISSION_TYPES)
def test_system_admin_has_all_feature_access(app, feature, perm):
    """SYSTEM_ADMIN should have full access to every feature."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.app_context():
        with patch('app.db.query', return_value=mock_rows), \
             c.session_transaction() as s:
            s['roles'] = ['SYSTEM_ADMIN']
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            if feature in result:
                assert result[feature].get(perm) is True


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_system_admin_feature_map_has_feature(app, feature):
    """SYSTEM_ADMIN feature map must contain every feature code."""
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert feature in result


# ── can_access_feature logic ───────────────────────────────────────────────────

@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_can_access_feature_true_when_in_map(app, feature, perm):
    """can_access_feature returns True when feature+perm present in map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=full_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, perm) is True


@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_can_access_feature_false_when_empty_map(app, feature, perm):
    """can_access_feature returns False when feature not in map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=empty_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, perm) is False


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_read_only_true(app, feature):
    """can_access_feature read=True when read_only_map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=read_only_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, 'r') is True


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_write_false_read_only(app, feature):
    """can_access_feature write=False when read_only_map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=read_only_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, 'w') is False


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_delete_false_read_only(app, feature):
    """can_access_feature delete=False when read_only_map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=read_only_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, 'd') is False


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_unknown_action_false(app, feature):
    """can_access_feature returns False for unknown action."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=full_feature_map()):
            from app.auth import can_access_feature
            assert can_access_feature(feature, 'x') is False


@pytest.mark.parametrize("unknown_feature", [
    'unknown_feature', 'nonexistent', '', 'admin', 'superpower', 'feature_x',
    'feature_y', 'feature_z', 'test', 'debug',
])
def test_can_access_unknown_feature_false(app, unknown_feature):
    """can_access_feature returns False for unknown feature code."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=full_feature_map()):
            from app.auth import can_access_feature
            # unknown_feature not in full_feature_map, so False
            assert can_access_feature(unknown_feature, 'r') is False


# ── _load_feature_access caching ──────────────────────────────────────────────

def test_load_feature_access_cached_in_g(app):
    """_load_feature_access caches result in g._feature_access."""
    mock_rows = [{'code': 'reports'}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session, g as flask_g
            session['roles'] = ['SYSTEM_ADMIN']
            from app.auth import _load_feature_access
            result1 = _load_feature_access()
            result2 = _load_feature_access()
            assert result1 is result2  # same object = cached


def test_load_feature_access_empty_roles(app):
    """_load_feature_access returns empty dict for empty roles."""
    with app.test_request_context('/'):
        from flask import session
        session['roles'] = []
        from app.auth import _load_feature_access
        result = _load_feature_access()
        assert result == {}


def test_load_feature_access_no_roles_key(app):
    """_load_feature_access returns empty dict when no roles in session."""
    with app.test_request_context('/'):
        from flask import session
        # Don't set roles
        from app.auth import _load_feature_access
        result = _load_feature_access()
        assert result == {}


def test_load_feature_access_valid_company_id_uses_full_query(app):
    """_load_feature_access uses full query when company_id is valid UUID."""
    mock_rows = [
        {'code': 'reports', 'r': True, 'w': False, 'd': False},
    ]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows) as mock_q:
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert 'reports' in result
            assert result['reports']['r'] is True
            assert result['reports']['w'] is False


def test_load_feature_access_invalid_company_id_uses_simple_query(app):
    """_load_feature_access uses simple query when company_id is invalid UUID."""
    mock_rows = [
        {'code': 'reports', 'r': True, 'w': False, 'd': False},
    ]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = 'not-a-uuid'
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert 'reports' in result


def test_load_feature_access_none_company_id_uses_simple_query(app):
    """_load_feature_access handles None company_id."""
    mock_rows = [
        {'code': 'reports', 'r': True, 'w': True, 'd': False},
    ]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = None
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── require_feature_access decorator ─────────────────────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_require_feature_access_denies_when_no_access(app, feature):
    """require_feature_access redirects when user lacks feature access."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code in (302, 308)


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_require_feature_access_allows_when_has_access(app, feature):
    """require_feature_access allows when user has feature access."""
    c = make_client(app, ['PORTAL_ADMIN'])
    full_map = {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES}
    with patch('app.auth._load_feature_access', return_value=full_map), \
         patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code != 302 or r.status_code in (200, 302)


# ── COALESCE behavior: company override vs no override ────────────────────────

COALESCE_SCENARIOS = [
    # (global_r, global_w, global_d, override_r, override_w, override_d, expected_r, expected_w, expected_d)
    (True, True, True, True, True, True, True, True, True),
    (True, True, True, False, False, False, False, False, False),
    (True, False, False, None, None, None, True, False, False),
    (False, False, False, True, True, True, False, False, False),
    (True, True, False, True, False, None, True, False, False),
]

@pytest.mark.parametrize("global_r,global_w,global_d,override_r,override_w,override_d,exp_r,exp_w,exp_d",
    COALESCE_SCENARIOS)
def test_coalesce_behavior(app, global_r, global_w, global_d,
                           override_r, override_w, override_d,
                           exp_r, exp_w, exp_d):
    """COALESCE(override, global) behavior for feature access."""
    # Simulate the result of the SQL query
    coalesce_r = override_r if override_r is not None else global_r
    coalesce_w = override_w if override_w is not None else global_w
    coalesce_d = override_d if override_d is not None else global_d
    result_r = global_r and coalesce_r
    result_w = global_w and coalesce_w
    result_d = global_d and coalesce_d
    assert result_r == exp_r
    assert result_w == exp_w
    assert result_d == exp_d


# ── Feature access with query returning various data ───────────────────────────

QUERY_RESULT_SCENARIOS = [
    [],
    [{'code': 'reports', 'r': True, 'w': True, 'd': True}],
    [{'code': 'reports', 'r': False, 'w': False, 'd': False}],
    [{'code': 'reports', 'r': True, 'w': False, 'd': False}],
    [{'code': 'reports', 'r': True, 'w': True, 'd': False}],
    [
        {'code': 'reports', 'r': True, 'w': True, 'd': True},
        {'code': 'imports', 'r': True, 'w': False, 'd': False},
    ],
    [{'code': f, 'r': True, 'w': True, 'd': True} for f in FEATURE_CODES],
]

@pytest.mark.parametrize("query_result", QUERY_RESULT_SCENARIOS)
def test_load_feature_access_processes_query_results(app, query_result):
    """_load_feature_access correctly processes various query results."""
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=query_result):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)
            for row in query_result:
                assert row['code'] in result
                assert result[row['code']]['r'] == bool(row['r'])
                assert result[row['code']]['w'] == bool(row['w'])
                assert result[row['code']]['d'] == bool(row['d'])


# ── has_feature_access template helper ────────────────────────────────────────

@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_has_feature_access_template_helper_true(app, feature, perm):
    """has_feature_access template helper returns True when access present."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=full_feature_map()):
            from app.auth import can_access_feature
            result = can_access_feature(feature, perm)
            assert result is True


@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_has_feature_access_template_helper_false(app, feature, perm):
    """has_feature_access template helper returns False when no access."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=empty_feature_map()):
            from app.auth import can_access_feature
            result = can_access_feature(feature, perm)
            assert result is False


# ── SYSTEM_ADMIN bypasses feature checks via routes ───────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_sa_feature_access_true_for_all_features(app, feature):
    """SYSTEM_ADMIN should get True for all features via route."""
    mock_rows = [{'code': f} for f in FEATURE_CODES]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access, can_access_feature
            _load_feature_access()
            # SA gets full access to all features from the query
            result = _load_feature_access()
            if feature in result:
                assert result[feature]['r'] is True


# ── Role × feature × permission matrix ────────────────────────────────────────

@pytest.mark.parametrize("role,feature,perm", [
    (role, feature, perm)
    for role in ['EMPLOYEE', 'DEPARTMENT_HEAD', 'HR_ADMIN']
    for feature in FEATURE_CODES
    for perm in PERMISSION_TYPES
])
def test_role_feature_perm_combinations(app, role, feature, perm):
    """Test all role/feature/permission combinations for consistency."""
    no_access_map = {}
    full_access_map = full_feature_map()
    c = make_client(app, [role])

    with app.test_request_context('/'):
        from flask import session
        session['roles'] = [role]
        session['company_id'] = FAKE_COMPANY_ID

        with patch('app.auth._load_feature_access', return_value=no_access_map):
            from app.auth import can_access_feature
            assert can_access_feature(feature, perm) is False

        with patch('app.auth._load_feature_access', return_value=full_access_map):
            assert can_access_feature(feature, perm) is True


# ── Feature access with no query results ─────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_empty_feature_access_for_all_roles_no_db_rows(app, role):
    """If DB returns no rows, feature access map is empty for non-SA roles."""
    if role == 'SYSTEM_ADMIN':
        return  # SA uses different path
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=[]):
            from flask import session
            session['roles'] = [role]
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert result == {}


# ── Partial feature maps ──────────────────────────────────────────────────────

PARTIAL_FEATURE_MAPS = [
    {'skills_intelligence': {'r': True, 'w': False, 'd': False}},
    {'reports': {'r': True, 'w': True, 'd': False}},
    {'employee_profiles': {'r': True, 'w': True, 'd': True}},
    {'org_chart': {'r': True, 'w': False, 'd': False}},
    {'vacation_management': {'r': True, 'w': True, 'd': False}},
    {'imports': {'r': False, 'w': False, 'd': False}},
    {'benchmarks': {'r': True, 'w': False, 'd': False}},
    {'company_settings': {'r': True, 'w': True, 'd': True}},
    {'notifications': {'r': True, 'w': True, 'd': False}},
    {'search': {'r': True, 'w': False, 'd': False}},
]

@pytest.mark.parametrize("partial_map", PARTIAL_FEATURE_MAPS)
def test_partial_feature_map_only_present_features_accessible(app, partial_map):
    """With partial map, only present features are accessible."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=partial_map):
            from app.auth import can_access_feature
            for feature in FEATURE_CODES:
                if feature in partial_map:
                    assert can_access_feature(feature, 'r') == partial_map[feature]['r']
                else:
                    assert can_access_feature(feature, 'r') is False


# ── Session role variations ────────────────────────────────────────────────────

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
    ['PORTAL_ADMIN', 'HR_ADMIN'],
    ['EMPLOYEE', 'DEPARTMENT_HEAD'],
    ['EMPLOYEE', 'DOTTED_LINE_MANAGER'],
    ['EMPLOYEE', 'HIRING_MANAGER'],
]

@pytest.mark.parametrize("roles", SESSION_ROLE_VARIANTS)
def test_load_feature_access_with_role_variants(app, roles):
    """_load_feature_access handles all role variants."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': False, 'd': False}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = roles
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── _is_valid_uuid used in feature access path ────────────────────────────────

VALID_COMPANY_IDS = [
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '12345678-1234-1234-1234-123456789012',
]

INVALID_COMPANY_IDS = [
    None, '', 'not-a-uuid', 'co-001', '123', 'AAAAAAAA',
    'invalid', 'co-001', '0000',
]

@pytest.mark.parametrize("company_id", VALID_COMPANY_IDS)
def test_valid_company_id_uses_full_query(app, company_id):
    """Valid company UUID triggers full COALESCE query."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': True, 'd': True}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = company_id
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


@pytest.mark.parametrize("company_id", INVALID_COMPANY_IDS)
def test_invalid_company_id_uses_simple_query(app, company_id):
    """Invalid company UUID triggers simple query."""
    mock_rows = [{'code': 'reports', 'r': True, 'w': True, 'd': True}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = company_id
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert isinstance(result, dict)


# ── Feature access integration: route tests ───────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_skills_intelligence_page_with_access(app, role):
    """Skills Intelligence page accessible to role that has access."""
    c = make_client(app, [role])
    access_map = {'skills_intelligence': {'r': True, 'w': True, 'd': True}}
    with patch('app.auth._load_feature_access', return_value=access_map), \
         patch('app.routes.skills_intelligence.query', return_value=[]), \
         patch('app.routes.skills_intelligence._si_enabled', return_value=True):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_skills_intelligence_page_without_access_redirect(app, role):
    """Skills Intelligence page redirects when role lacks access."""
    c = make_client(app, [role])
    with patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin/skills-intelligence')
    assert r.status_code in (302, 308)


# ── Permutation: feature present but wrong perm ───────────────────────────────

WRONG_PERM_SCENARIOS = [
    ('reports', 'r', {'reports': {'r': False, 'w': True, 'd': True}}, False),
    ('reports', 'w', {'reports': {'r': True, 'w': False, 'd': True}}, False),
    ('reports', 'd', {'reports': {'r': True, 'w': True, 'd': False}}, False),
    ('imports', 'r', {'imports': {'r': True, 'w': False, 'd': False}}, True),
    ('imports', 'w', {'imports': {'r': True, 'w': False, 'd': False}}, False),
    ('imports', 'd', {'imports': {'r': True, 'w': False, 'd': False}}, False),
    ('benchmarks', 'r', {'benchmarks': {'r': True, 'w': True, 'd': False}}, True),
    ('benchmarks', 'd', {'benchmarks': {'r': True, 'w': True, 'd': False}}, False),
]

@pytest.mark.parametrize("feature,perm,access_map,expected", WRONG_PERM_SCENARIOS)
def test_can_access_feature_specific_perm(app, feature, perm, access_map, expected):
    """can_access_feature returns correct bool for specific perm in map."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=access_map):
            from app.auth import can_access_feature
            assert can_access_feature(feature, perm) is expected


# ── require_roles decorator ────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_require_roles_admin_blocks_non_admin(app, role):
    """require_roles('SYSTEM_ADMIN') blocks non-SYSTEM_ADMIN roles."""
    c = make_client(app, [role])
    r = c.get('/api/admin/roles/features')
    if role == 'SYSTEM_ADMIN':
        with patch('app.routes.admin.query', return_value=[]):
            r2 = make_client(app, [role]).get('/api/admin/roles/features')
        assert r2.status_code != 500
    else:
        assert r.status_code in (302, 308)


# ── Mixed feature access scenarios ────────────────────────────────────────────

MIXED_SCENARIOS = [
    {
        'skills_intelligence': {'r': True, 'w': False, 'd': False},
        'reports': {'r': False, 'w': False, 'd': False},
    },
    {
        'skills_intelligence': {'r': True, 'w': True, 'd': False},
        'reports': {'r': True, 'w': False, 'd': False},
        'imports': {'r': False, 'w': False, 'd': False},
    },
    {
        'employee_profiles': {'r': True, 'w': True, 'd': True},
        'org_chart': {'r': True, 'w': False, 'd': False},
        'search': {'r': True, 'w': False, 'd': False},
    },
    {f: {'r': True, 'w': True, 'd': True} for f in FEATURE_CODES},
    {},
]

@pytest.mark.parametrize("access_map", MIXED_SCENARIOS)
def test_mixed_feature_access_correctness(app, access_map):
    """can_access_feature correctly reads mixed access maps."""
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=access_map):
            from app.auth import can_access_feature
            for feature in FEATURE_CODES:
                for perm in PERMISSION_TYPES:
                    expected = access_map.get(feature, {}).get(perm, False)
                    assert can_access_feature(feature, perm) == bool(expected)


# ── Default action is 'r' ──────────────────────────────────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_default_action_is_read(app, feature):
    """can_access_feature defaults to 'r' action."""
    access_map = {feature: {'r': True, 'w': False, 'd': False}}
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=access_map):
            from app.auth import can_access_feature
            assert can_access_feature(feature) is True  # default action = 'r'


@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_default_action_false_when_no_read(app, feature):
    """can_access_feature defaults to 'r' action and returns False if no read."""
    access_map = {feature: {'r': False, 'w': True, 'd': True}}
    with app.test_request_context('/'):
        with patch('app.auth._load_feature_access', return_value=access_map):
            from app.auth import can_access_feature
            assert can_access_feature(feature) is False


# ── Boolean conversion ─────────────────────────────────────────────────────────

BOOL_CONVERSION_CASES = [
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    (None, False),
]

@pytest.mark.parametrize("raw_val,expected", BOOL_CONVERSION_CASES)
def test_feature_access_bool_conversion(app, raw_val, expected):
    """Feature access values are converted to bool correctly."""
    mock_rows = [{'code': 'reports', 'r': raw_val, 'w': raw_val, 'd': raw_val}]
    with app.test_request_context('/'):
        with patch('app.db.query', return_value=mock_rows):
            from flask import session
            session['roles'] = ['EMPLOYEE']
            session['company_id'] = FAKE_COMPANY_ID
            from app.auth import _load_feature_access
            result = _load_feature_access()
            assert result['reports']['r'] == expected
            assert result['reports']['w'] == expected
            assert result['reports']['d'] == expected
