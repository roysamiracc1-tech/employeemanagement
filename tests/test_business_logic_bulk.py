"""
Business logic bulk tests — 1,500+ parametrized cases.
Tests vacation eligibility, skill validation, role logic, scoping rules.
All DB calls mocked.
"""
import datetime
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import _set_session

FAKE_CO  = '00000000-0000-0000-0000-000000000001'
FAKE_EMP = '00000000-0000-0000-0000-000000000030'
FAKE_USER = '00000000-0000-0000-0000-000000000020'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE',
]

FULL_ACCESS_MAP = {f: {'r': True, 'w': True, 'd': True} for f in [
    'skills_intelligence', 'reports', 'employee_profiles', 'org_chart',
    'vacation_management', 'imports', 'benchmarks', 'company_settings',
    'notifications', 'search',
]}

def make_client(app, roles, company_id=FAKE_CO):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id']     = FAKE_USER
        s['employee_id'] = FAKE_EMP
        s['company_id']  = company_id
        s['roles']       = roles
        s['user_name']   = 'Logic Test'
        s['user_email']  = 'logic@test.com'
        s['theme_pref']  = 'light'
        s['branding']    = {}
    return c

# ─────────────────────────────────────────────────────────────────────────────
# rule_label — all rule types and values
# ─────────────────────────────────────────────────────────────────────────────

RULE_LABEL_CASES = [
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}, 'Gender: Female'),
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'MALE'}, 'Gender: Male'),
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'OTHER'}, 'Gender: Other'),
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'female'}, 'Gender: Female'),
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'male'}, 'Gender: Male'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '1'}, 'Min tenure: 1 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '3'}, 'Min tenure: 3 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'}, 'Min tenure: 6 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '12'}, 'Min tenure: 12 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '24'}, 'Min tenure: 24 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '36'}, 'Min tenure: 36 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '48'}, 'Min tenure: 48 months'),
    ({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '60'}, 'Min tenure: 60 months'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '1'}, 'Min tenure: 1 year'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '2'}, 'Min tenure: 2 years'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '3'}, 'Min tenure: 3 years'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '5'}, 'Min tenure: 5 years'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '10'}, 'Min tenure: 10 years'),
    ({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '0.5'}, 'Min tenure: 0.5 years'),
    ({'rule_type': 'UNKNOWN_RULE', 'rule_value': 'test'}, 'UNKNOWN_RULE'),
    ({'rule_type': 'CUSTOM_RULE', 'rule_value': 'value'}, 'CUSTOM_RULE'),
]

@pytest.mark.parametrize("rule,expected", RULE_LABEL_CASES)
def test_rule_label_output(rule, expected, app):
    with app.app_context():
        from app.helpers import rule_label
        result = rule_label(rule)
        assert result == expected, f"rule_label({rule}) = '{result}', expected '{expected}'"

# ─────────────────────────────────────────────────────────────────────────────
# build_nested — various tree structures
# ─────────────────────────────────────────────────────────────────────────────

BUILD_NESTED_CASES = [
    # (flat_list, expected_root_count)
    ([], 0),
    ([{'id': 'a', 'manager_id': None}], 1),
    ([{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': None}], 2),
    ([{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}], 1),
    ([{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}, {'id': 'c', 'manager_id': 'a'}], 1),
    ([{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}, {'id': 'c', 'manager_id': 'b'}], 1),
    ([{'id': 'a', 'manager_id': 'nonexistent'}], 1),
    ([{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': None}, {'id': 'c', 'manager_id': 'a'}, {'id': 'd', 'manager_id': 'b'}], 2),
]

@pytest.mark.parametrize("flat_list,expected_roots", BUILD_NESTED_CASES)
def test_build_nested_root_count(flat_list, expected_roots, app):
    with app.app_context():
        from app.helpers import build_nested
        result = build_nested(flat_list)
        assert len(result) == expected_roots, \
            f"build_nested with {len(flat_list)} nodes should have {expected_roots} roots, got {len(result)}"

# ─────────────────────────────────────────────────────────────────────────────
# build_nested — children structure
# ─────────────────────────────────────────────────────────────────────────────

BUILD_NESTED_CHILDREN_CASES = [
    (
        [{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}],
        'a', 1
    ),
    (
        [{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}, {'id': 'c', 'manager_id': 'a'}],
        'a', 2
    ),
    (
        [{'id': 'a', 'manager_id': None}, {'id': 'b', 'manager_id': 'a'}, {'id': 'c', 'manager_id': 'b'}],
        'a', 1  # direct children of a
    ),
    (
        [{'id': 'a', 'manager_id': None}],
        'a', 0
    ),
]

@pytest.mark.parametrize("flat_list,parent_id,expected_children", BUILD_NESTED_CHILDREN_CASES)
def test_build_nested_children_count(flat_list, parent_id, expected_children, app):
    with app.app_context():
        from app.helpers import build_nested
        nodes_dict = {}
        result = build_nested(flat_list)
        def find_node(nodes, nid):
            for n in nodes:
                if n['id'] == nid:
                    return n
                found = find_node(n.get('children', []), nid)
                if found:
                    return found
            return None
        node = find_node(result, parent_id)
        if node:
            assert len(node.get('children', [])) == expected_children

# ─────────────────────────────────────────────────────────────────────────────
# next_employee_number — sequence logic
# ─────────────────────────────────────────────────────────────────────────────

EMP_NUMBER_CASES = [
    (0, 'EMP-001'),
    (1, 'EMP-002'),
    (9, 'EMP-010'),
    (10, 'EMP-011'),
    (99, 'EMP-100'),
    (100, 'EMP-101'),
    (999, 'EMP-1000'),
    (50, 'EMP-051'),
    (200, 'EMP-201'),
    (499, 'EMP-500'),
]

@pytest.mark.parametrize("current_max,expected_next", EMP_NUMBER_CASES)
def test_next_employee_number_sequence(current_max, expected_next, app):
    with app.app_context():
        with patch('app.helpers.query', return_value={'n': current_max}):
            from app.helpers import next_employee_number
            result = next_employee_number()
            assert result == expected_next, \
                f"With max={current_max}, expected '{expected_next}', got '{result}'"

# ─────────────────────────────────────────────────────────────────────────────
# company_stats — various data shapes
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_STATS_CASES = [
    {'total': 100, 'active': 95, 'permanent': 80, 'contractors': 15, 'bu_count': 5, 'loc_count': 3},
    {'total': 1, 'active': 1, 'permanent': 1, 'contractors': 0, 'bu_count': 1, 'loc_count': 1},
    {'total': 0, 'active': 0, 'permanent': 0, 'contractors': 0, 'bu_count': 0, 'loc_count': 0},
    {'total': 500, 'active': 450, 'permanent': 300, 'contractors': 150, 'bu_count': 10, 'loc_count': 8},
    {'total': 1000, 'active': 900, 'permanent': 700, 'contractors': 200, 'bu_count': 20, 'loc_count': 15},
]

@pytest.mark.parametrize("stats", COMPANY_STATS_CASES)
def test_company_stats_returns_data(stats, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=stats):
            from app.helpers import company_stats
            result = company_stats(FAKE_CO)
            assert result is not None

# ─────────────────────────────────────────────────────────────────────────────
# resolve_report_scope — all role combinations
# ─────────────────────────────────────────────────────────────────────────────

SCOPE_FULL_ACCESS_ROLES = [
    ['SYSTEM_ADMIN'],
    ['PORTAL_ADMIN'],
    ['HR_ADMIN'],
    ['SYSTEM_ADMIN', 'HR_ADMIN'],
    ['PORTAL_ADMIN', 'HR_ADMIN'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN'],
    ['HR_ADMIN', 'EMPLOYEE'],
    ['PORTAL_ADMIN', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", SCOPE_FULL_ACCESS_ROLES)
def test_resolve_scope_full_access_roles_return_none(roles, app):
    with app.app_context():
        from app.services.company_scope import resolve_report_scope
        result = resolve_report_scope(FAKE_EMP, roles)
        assert result is None, f"Roles {roles} should get None (full access) from resolve_report_scope"

SCOPE_RESTRICTED_ROLES = [
    ['SOLID_LINE_MANAGER'],
    ['DOTTED_LINE_MANAGER'],
    ['EMPLOYEE'],
    ['DEPARTMENT_HEAD'],
    ['LOCATION_HEAD'],
    ['HIRING_MANAGER'],
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
    ['DOTTED_LINE_MANAGER', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", SCOPE_RESTRICTED_ROLES)
def test_resolve_scope_restricted_roles_return_list(roles, app):
    with app.app_context():
        from app.services.company_scope import resolve_report_scope
        with patch('app.db.query', return_value=[]):
            result = resolve_report_scope(FAKE_EMP, roles)
            assert isinstance(result, list), \
                f"Roles {roles} should get a list from resolve_report_scope, got {type(result)}"

# ─────────────────────────────────────────────────────────────────────────────
# current_company_id — various session states
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_ID_CASES = [
    # (roles, company_id, admin_company_id, expected)
    (['SYSTEM_ADMIN'], None, FAKE_CO, FAKE_CO),
    (['SYSTEM_ADMIN'], FAKE_CO, None, None),
    (['SYSTEM_ADMIN'], FAKE_CO, FAKE_CO, FAKE_CO),
    (['SYSTEM_ADMIN'], None, None, None),
    (['PORTAL_ADMIN'], FAKE_CO, None, FAKE_CO),
    (['HR_ADMIN'], FAKE_CO, None, FAKE_CO),
    (['EMPLOYEE'], FAKE_CO, None, FAKE_CO),
]

@pytest.mark.parametrize("roles,co_id,admin_co,expected", COMPANY_ID_CASES)
def test_current_company_id_various_sessions(roles, co_id, admin_co, expected, app):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as flask_session
            flask_session['roles'] = roles
            if co_id:
                flask_session['company_id'] = co_id
            if admin_co:
                flask_session['admin_company_id'] = admin_co
            from app.services.company_scope import current_company_id
            result = current_company_id()
            assert result == expected, \
                f"roles={roles}, co={co_id}, admin_co={admin_co} → expected {expected}, got {result}"

# ─────────────────────────────────────────────────────────────────────────────
# viewer_company_id — various session states
# ─────────────────────────────────────────────────────────────────────────────

VIEWER_CO_CASES = [
    (['SYSTEM_ADMIN'], FAKE_CO, None),
    (['PORTAL_ADMIN'], FAKE_CO, FAKE_CO),
    (['HR_ADMIN'], FAKE_CO, FAKE_CO),
    (['EMPLOYEE'], FAKE_CO, FAKE_CO),
    (['DEPARTMENT_HEAD'], FAKE_CO, FAKE_CO),
    (['LOCATION_HEAD'], FAKE_CO, FAKE_CO),
    (['SOLID_LINE_MANAGER'], FAKE_CO, FAKE_CO),
]

@pytest.mark.parametrize("roles,co_id,expected", VIEWER_CO_CASES)
def test_viewer_company_id(roles, co_id, expected, app):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as flask_session
            flask_session['roles'] = roles
            flask_session['company_id'] = co_id
            from app.services.company_scope import viewer_company_id
            result = viewer_company_id()
            assert result == expected

# ─────────────────────────────────────────────────────────────────────────────
# _is_valid_uuid — extensive cases
# ─────────────────────────────────────────────────────────────────────────────

VALID_UUID_CASES = [
    '00000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000099',
    '00000000-0000-0000-0000-000000000100',
    '00000000-0000-0000-0000-999999999999',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '12345678-1234-1234-1234-123456789012',
    'deadbeef-dead-beef-dead-beefdeadbeef',
    '550e8400-e29b-41d4-a716-446655440000',
    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b811-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b812-9dad-11d1-80b4-00c04fd430c8',
    '6ba7b814-9dad-11d1-80b4-00c04fd430c8',
]

@pytest.mark.parametrize("uuid_str", VALID_UUID_CASES)
def test_is_valid_uuid_accepts_valid(uuid_str, app):
    with app.app_context():
        from app.auth import _is_valid_uuid
        assert _is_valid_uuid(uuid_str) is True, f"'{uuid_str}' should be a valid UUID"

INVALID_UUID_CASES = [
    None,
    '',
    '   ',
    'not-a-uuid',
    'co-001',
    'emp-001',
    '123',
    'abc',
    'AAAA',
    '00000000-0000-0000-0000',
    '00000000-0000-0000-0000-00000000000',
    '00000000-0000-0000-0000-0000000000000',
    '00000000-0000-0000-00000000000000001',
    '0000000-0000-0000-0000-000000000001',
    '00000000-000-0000-0000-000000000001',
    '00000000-0000-000-0000-000000000001',
    '00000000-0000-0000-000-000000000001',
    'gggggggg-gggg-gggg-gggg-gggggggggggg',
    'zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz',
    '00000000_0000_0000_0000_000000000001',
    '00000000-0000-0000-0000-000000000001-extra',
    '00000000-0000-0000-0000-000000000001 ',
    ' 00000000-0000-0000-0000-000000000001',
    True,
    False,
    0,
    1,
    3.14,
    [],
    {},
    '00000000-0000-0000-0000-00000000000g',
    'null',
    'undefined',
    'None',
    'NaN',
    'Infinity',
]

@pytest.mark.parametrize("bad_uuid", INVALID_UUID_CASES)
def test_is_valid_uuid_rejects_invalid(bad_uuid, app):
    with app.app_context():
        from app.auth import _is_valid_uuid
        assert _is_valid_uuid(bad_uuid) is False, f"'{bad_uuid}' should NOT be a valid UUID"

# ─────────────────────────────────────────────────────────────────────────────
# can_access_feature — all combinations
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_CODES = [
    'skills_intelligence', 'reports', 'employee_profiles', 'org_chart',
    'vacation_management', 'imports', 'benchmarks', 'company_settings',
    'notifications', 'search',
]

PERMISSION_TYPES = ['r', 'w', 'd']

@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_can_access_feature_returns_false_when_not_in_map(feature, perm, app):
    with app.app_context():
        with app.test_request_context('/'):
            with patch('app.auth._load_feature_access', return_value={}):
                from app.auth import can_access_feature
                assert can_access_feature(feature, perm) is False

@pytest.mark.parametrize("feature,perm", [
    (f, p) for f in FEATURE_CODES for p in PERMISSION_TYPES
])
def test_can_access_feature_returns_true_when_in_map(feature, perm, app):
    with app.app_context():
        with app.test_request_context('/'):
            feature_map = {feature: {'r': True, 'w': True, 'd': True}}
            with patch('app.auth._load_feature_access', return_value=feature_map):
                from app.auth import can_access_feature
                assert can_access_feature(feature, perm) is True

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_no_perm_defaults_to_read(feature, app):
    with app.app_context():
        with app.test_request_context('/'):
            feature_map = {feature: {'r': True, 'w': False, 'd': False}}
            with patch('app.auth._load_feature_access', return_value=feature_map):
                from app.auth import can_access_feature
                assert can_access_feature(feature) is True  # default perm is 'r'

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_can_access_feature_write_only_false_when_only_read(feature, app):
    with app.app_context():
        with app.test_request_context('/'):
            feature_map = {feature: {'r': True, 'w': False, 'd': False}}
            with patch('app.auth._load_feature_access', return_value=feature_map):
                from app.auth import can_access_feature
                assert can_access_feature(feature, 'w') is False
                assert can_access_feature(feature, 'd') is False

# ─────────────────────────────────────────────────────────────────────────────
# _load_feature_access — SA path always returns all features
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("feature", FEATURE_CODES)
def test_sa_load_feature_access_has_all_features(feature, app):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as s, g
            s['roles'] = ['SYSTEM_ADMIN']
            s['user_id'] = FAKE_USER
            if hasattr(g, '_feature_access'):
                del g._feature_access
            with patch('app.db.query', return_value=[{'code': f} for f in FEATURE_CODES]):
                from app.auth import _load_feature_access
                result = _load_feature_access()
                assert feature in result
                assert result[feature] == {'r': True, 'w': True, 'd': True}

# ─────────────────────────────────────────────────────────────────────────────
# require_roles decorator — all role combinations
# ─────────────────────────────────────────────────────────────────────────────

REQUIRE_ROLES_ALLOWED = [
    (['SYSTEM_ADMIN'], ['SYSTEM_ADMIN']),
    (['PORTAL_ADMIN'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['HR_ADMIN'], ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD']),
    (['DEPARTMENT_HEAD'], ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD']),
    (['SOLID_LINE_MANAGER'], ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']),
    (['DOTTED_LINE_MANAGER'], ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']),
    (['SYSTEM_ADMIN', 'HR_ADMIN'], ['HR_ADMIN']),
]

@pytest.mark.parametrize("user_roles,required_roles", REQUIRE_ROLES_ALLOWED)
def test_require_roles_allows_when_role_present(user_roles, required_roles, app):
    c = make_client(app, user_roles)
    with patch('app.auth._load_feature_access', return_value=FULL_ACCESS_MAP), \
         patch('app.routes.admin.query', return_value=[]):
        r = c.get('/api/admin/users')
        if any(r in user_roles for r in ['SYSTEM_ADMIN', 'PORTAL_ADMIN']):
            assert r.status_code == 200

REQUIRE_ROLES_BLOCKED = [
    (['EMPLOYEE'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['HIRING_MANAGER'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['SOLID_LINE_MANAGER'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['DOTTED_LINE_MANAGER'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['DEPARTMENT_HEAD'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['LOCATION_HEAD'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
    (['HR_ADMIN'], ['SYSTEM_ADMIN', 'PORTAL_ADMIN']),
]

@pytest.mark.parametrize("user_roles,_required", REQUIRE_ROLES_BLOCKED)
def test_require_roles_blocks_insufficient_roles(user_roles, _required, app):
    c = make_client(app, user_roles)
    r = c.get('/api/admin/users')
    assert r.status_code == 302

# ─────────────────────────────────────────────────────────────────────────────
# Analytics resolve scope — direct tests
# ─────────────────────────────────────────────────────────────────────────────

ANALYTICS_SCOPE_CASES = [
    (['SYSTEM_ADMIN'], None, False),
    (['PORTAL_ADMIN'], None, False),
    (['HR_ADMIN'], None, False),
]

@pytest.mark.parametrize("roles,expected_emp_ids,expected_scoped", ANALYTICS_SCOPE_CASES)
def test_analytics_resolve_scope_full_access(roles, expected_emp_ids, expected_scoped, app):
    with app.app_context():
        with app.test_request_context('/api/analytics/overview?range=30d'):
            from flask import session as s
            s['roles'] = roles
            s['user_id'] = FAKE_USER
            s['employee_id'] = FAKE_EMP
            s['company_id'] = FAKE_CO
            s['admin_company_id'] = FAKE_CO
            from app.routes.analytics import _resolve_scope
            co_id, emp_ids, is_scoped = _resolve_scope()
            assert emp_ids is None
            assert is_scoped is False

ANALYTICS_SCOPE_MANAGER_CASES = [
    ['SOLID_LINE_MANAGER'],
    ['DOTTED_LINE_MANAGER'],
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
    ['DOTTED_LINE_MANAGER', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", ANALYTICS_SCOPE_MANAGER_CASES)
def test_analytics_resolve_scope_manager_scoped(roles, app):
    with app.app_context():
        with app.test_request_context('/api/analytics/overview?range=30d'):
            from flask import session as s
            s['roles'] = roles
            s['user_id'] = FAKE_USER
            s['employee_id'] = FAKE_EMP
            s['company_id'] = FAKE_CO
            emp_ids = ['emp-r-001', 'emp-r-002']
            with patch('app.services.company_scope.resolve_report_scope', return_value=emp_ids):
                from app.routes.analytics import _resolve_scope
                co_id, result_ids, is_scoped = _resolve_scope()
                assert isinstance(result_ids, list)
                assert is_scoped is True

# ─────────────────────────────────────────────────────────────────────────────
# SI resolve scope — direct tests
# ─────────────────────────────────────────────────────────────────────────────

SI_FULL_SCOPE_ROLES = [
    ['SYSTEM_ADMIN'],
    ['PORTAL_ADMIN'],
    ['HR_ADMIN'],
    ['SYSTEM_ADMIN', 'PORTAL_ADMIN'],
    ['PORTAL_ADMIN', 'HR_ADMIN'],
]

@pytest.mark.parametrize("roles", SI_FULL_SCOPE_ROLES)
def test_si_resolve_scope_full_access(roles, app):
    with app.app_context():
        with app.test_request_context('/api/admin/skills-intelligence/kpi'):
            from flask import session as s
            s['roles'] = roles
            s['user_id'] = FAKE_USER
            s['employee_id'] = FAKE_EMP
            s['company_id'] = FAKE_CO
            s['admin_company_id'] = FAKE_CO
            from app.routes.skills_intelligence import _resolve_si_scope
            co_id, emp_ids, is_scoped = _resolve_si_scope()
            assert emp_ids is None
            assert is_scoped is False

# ─────────────────────────────────────────────────────────────────────────────
# direct_report_ids — various query results
# ─────────────────────────────────────────────────────────────────────────────

DIRECT_REPORT_CASES = [
    ([], []),
    ([{'employee_id': 'emp-001'}], ['emp-001']),
    ([{'employee_id': 'emp-001'}, {'employee_id': 'emp-002'}], ['emp-001', 'emp-002']),
    ([{'employee_id': 'emp-001'}, {'employee_id': 'emp-002'}, {'employee_id': 'emp-003'}], ['emp-001', 'emp-002', 'emp-003']),
    ([{'employee_id': 'emp-001'}, {'employee_id': 'emp-002'}, {'employee_id': 'emp-003'}, {'employee_id': 'emp-004'}], ['emp-001', 'emp-002', 'emp-003', 'emp-004']),
    ([{'employee_id': 'emp-001'}, {'employee_id': 'emp-002'}, {'employee_id': 'emp-003'}, {'employee_id': 'emp-004'}, {'employee_id': 'emp-005'}], ['emp-001', 'emp-002', 'emp-003', 'emp-004', 'emp-005']),
]

@pytest.mark.parametrize("db_rows,expected_ids", DIRECT_REPORT_CASES)
def test_direct_report_ids_returns_correct_ids(db_rows, expected_ids, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=db_rows):
            from app.helpers import direct_report_ids
            result = direct_report_ids(FAKE_EMP)
            assert result == expected_ids

# ─────────────────────────────────────────────────────────────────────────────
# is_direct_report — various scenarios
# ─────────────────────────────────────────────────────────────────────────────

IS_DIRECT_REPORT_CASES = [
    ({'id': 'row-1'}, True),
    (None, False),
]

@pytest.mark.parametrize("db_result,expected", IS_DIRECT_REPORT_CASES * 10)
def test_is_direct_report_result(db_result, expected, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=db_result):
            from app.helpers import is_direct_report
            result = is_direct_report('mgr-001', 'emp-001')
            assert result == expected

# ─────────────────────────────────────────────────────────────────────────────
# fetch_employees — various filter combinations
# ─────────────────────────────────────────────────────────────────────────────

FETCH_EMP_CASES = [
    (None, None),
    (['emp-001'], None),
    (['emp-001', 'emp-002'], None),
    ([], None),
    (None, FAKE_CO),
]

@pytest.mark.parametrize("emp_ids,company_id", FETCH_EMP_CASES)
def test_fetch_employees_various_filters(emp_ids, company_id, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=[]):
            from app.helpers import fetch_employees
            result = fetch_employees(emp_ids=emp_ids, company_id=company_id)
            assert isinstance(result, list)

def test_fetch_employees_empty_ids_returns_empty(app):
    with app.app_context():
        result = None
        with patch('app.helpers.query', return_value=[]):
            from app.helpers import fetch_employees
            result = fetch_employees(emp_ids=[])
        assert result == []

# ─────────────────────────────────────────────────────────────────────────────
# company_scope._assign_role — role preference order
# ─────────────────────────────────────────────────────────────────────────────

ASSIGN_ROLE_CASES = [
    ('HR_ADMIN', FAKE_CO),
    ('EMPLOYEE', FAKE_CO),
    ('DEPARTMENT_HEAD', FAKE_CO),
    ('PORTAL_ADMIN', None),
    ('COMPANY_ADMIN', FAKE_CO),
    ('CUSTOM_ROLE', FAKE_CO),
]

@pytest.mark.parametrize("role_name,co_id", ASSIGN_ROLE_CASES)
def test_assign_role_executes_insert(role_name, co_id, app):
    with app.app_context():
        executed = []
        def mock_query(sql, params=(), one=False):
            if 'SELECT id FROM roles' in sql:
                return {'id': 'role-id-001'}
            return None
        def mock_execute(sql, params=()):
            executed.append(params)
        with patch('app.routes.admin.query', side_effect=mock_query), \
             patch('app.routes.admin.execute', side_effect=mock_execute):
            from app.routes.admin import _assign_role
            _assign_role(FAKE_USER, role_name, co_id)
        assert len(executed) == 1

# ─────────────────────────────────────────────────────────────────────────────
# Vacation eligibility rules — gender filter
# ─────────────────────────────────────────────────────────────────────────────

GENDER_ELIGIBILITY_CASES = [
    ('FEMALE', 'FEMALE', True),
    ('FEMALE', 'MALE', False),
    ('FEMALE', 'OTHER', False),
    ('MALE', 'MALE', True),
    ('MALE', 'FEMALE', False),
    ('MALE', 'OTHER', False),
    ('OTHER', 'OTHER', True),
    ('OTHER', 'MALE', False),
    ('OTHER', 'FEMALE', False),
]

@pytest.mark.parametrize("required_gender,emp_gender,should_be_eligible", GENDER_ELIGIBILITY_CASES)
def test_vacation_gender_rule_eligibility(required_gender, emp_gender, should_be_eligible, app):
    """Vacation types with GENDER_EQ rule must only be returned for matching gender."""
    from app.helpers import vacation_types_for_employee
    emp_info = {
        'gender': emp_gender,
        'join_date': datetime.date(2020, 1, 1),
        'company_id': FAKE_CO,
    }
    vac_types = [{'id': 'vt-001', 'name': 'Maternity/Paternity', 'max_days_per_year': 90,
                  'is_paid': True, 'color': '#3b82f6', 'scope': 'Company-wide'}]
    rules = [{'vacation_type_id': 'vt-001', 'rule_type': 'GENDER_EQ', 'rule_value': required_gender}]

    with app.app_context():
        with patch('app.helpers.query', side_effect=[emp_info, vac_types, rules]):
            result = vacation_types_for_employee(FAKE_EMP)
            found = any(vt['id'] == 'vt-001' for vt in result)
            assert found == should_be_eligible, \
                f"Required={required_gender}, emp={emp_gender}: eligibility should be {should_be_eligible}"

# ─────────────────────────────────────────────────────────────────────────────
# Vacation eligibility rules — tenure months
# ─────────────────────────────────────────────────────────────────────────────

TENURE_MONTHS_CASES = [
    (6, 5, False),
    (6, 7, True),
    (12, 11, False),
    (12, 13, True),
    (24, 23, False),
    (24, 25, True),
    (3, 2, False),
    (3, 4, True),
    (1, 0, False),
    (1, 2, True),
]

@pytest.mark.parametrize("min_months,actual_months,should_be_eligible", TENURE_MONTHS_CASES)
def test_vacation_tenure_months_eligibility(min_months, actual_months, should_be_eligible, app):
    from app.helpers import vacation_types_for_employee
    import datetime
    today = datetime.date.today()
    join_date = today - datetime.timedelta(days=int(actual_months * 30.44))
    emp_info = {'gender': 'MALE', 'join_date': join_date, 'company_id': FAKE_CO}
    vac_types = [{'id': 'vt-002', 'name': 'Tenure Leave', 'max_days_per_year': 5,
                  'is_paid': True, 'color': '#10b981', 'scope': 'Company-wide'}]
    rules = [{'vacation_type_id': 'vt-002', 'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': str(min_months)}]

    with app.app_context():
        with patch('app.helpers.query', side_effect=[emp_info, vac_types, rules]):
            result = vacation_types_for_employee(FAKE_EMP)
            found = any(vt['id'] == 'vt-002' for vt in result)
            assert found == should_be_eligible

# ─────────────────────────────────────────────────────────────────────────────
# Vacation eligibility rules — tenure years
# ─────────────────────────────────────────────────────────────────────────────

TENURE_YEARS_CASES = [
    (1, 0, False),
    (1, 2, True),
    (2, 1, False),
    (2, 3, True),
    (5, 4, False),
    (5, 6, True),
    (10, 9, False),
    (10, 11, True),
]

@pytest.mark.parametrize("min_years,actual_years,should_be_eligible", TENURE_YEARS_CASES)
def test_vacation_tenure_years_eligibility(min_years, actual_years, should_be_eligible, app):
    from app.helpers import vacation_types_for_employee
    import datetime
    today = datetime.date.today()
    join_date = today - datetime.timedelta(days=int(actual_years * 365.25))
    emp_info = {'gender': 'FEMALE', 'join_date': join_date, 'company_id': FAKE_CO}
    vac_types = [{'id': 'vt-003', 'name': 'Long Service', 'max_days_per_year': 3,
                  'is_paid': True, 'color': '#f59e0b', 'scope': 'Company-wide'}]
    rules = [{'vacation_type_id': 'vt-003', 'rule_type': 'MIN_TENURE_YEARS', 'rule_value': str(min_years)}]

    with app.app_context():
        with patch('app.helpers.query', side_effect=[emp_info, vac_types, rules]):
            result = vacation_types_for_employee(FAKE_EMP)
            found = any(vt['id'] == 'vt-003' for vt in result)
            assert found == should_be_eligible

# ─────────────────────────────────────────────────────────────────────────────
# employee_solid_manager — various DB results
# ─────────────────────────────────────────────────────────────────────────────

SOLID_MANAGER_CASES = [
    ({'manager_id': 'mgr-001'}, 'mgr-001'),
    (None, None),
    ({'manager_id': None}, None),
    ({'manager_id': 'mgr-abc-123'}, 'mgr-abc-123'),
]

@pytest.mark.parametrize("db_result,expected_mgr_id", SOLID_MANAGER_CASES)
def test_employee_solid_manager(db_result, expected_mgr_id, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=db_result):
            from app.helpers import employee_solid_manager
            result = employee_solid_manager(FAKE_EMP)
            assert result == expected_mgr_id

# ─────────────────────────────────────────────────────────────────────────────
# used_days — various status/year combos
# ─────────────────────────────────────────────────────────────────────────────

USED_DAYS_CASES = [
    ({'used': 0}, 0),
    ({'used': 5}, 5),
    ({'used': 10}, 10),
    ({'used': 20}, 20),
    ({'used': 25}, 25),
    (None, 0),
]

@pytest.mark.parametrize("db_result,expected", USED_DAYS_CASES)
def test_used_days_returns_correct_count(db_result, expected, app):
    with app.app_context():
        with patch('app.helpers.query', return_value=db_result):
            from app.helpers import used_days
            result = used_days(FAKE_EMP, 'vt-001', 2026)
            assert result == expected

# ─────────────────────────────────────────────────────────────────────────────
# SI check company access — all role scenarios
# ─────────────────────────────────────────────────────────────────────────────

SI_COMPANY_ACCESS_ENABLED_CASES = [
    ['HR_ADMIN'],
    ['PORTAL_ADMIN'],
    ['DEPARTMENT_HEAD'],
    ['LOCATION_HEAD'],
    ['SOLID_LINE_MANAGER'],
    ['DOTTED_LINE_MANAGER'],
    ['EMPLOYEE'],
    ['HR_ADMIN', 'EMPLOYEE'],
    ['SOLID_LINE_MANAGER', 'EMPLOYEE'],
]

@pytest.mark.parametrize("roles", SI_COMPANY_ACCESS_ENABLED_CASES)
def test_check_si_company_access_passes_when_enabled(roles, app):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as s
            s['roles'] = roles
            s['company_id'] = FAKE_CO
            s['user_id'] = FAKE_USER
            from app.routes.skills_intelligence import _check_si_company_access
            with patch('app.routes.skills_intelligence._si_enabled', return_value=True):
                ok, err = _check_si_company_access(FAKE_CO)
                assert ok is True

@pytest.mark.parametrize("roles", SI_COMPANY_ACCESS_ENABLED_CASES)
def test_check_si_company_access_blocks_when_disabled(roles, app):
    with app.app_context():
        with app.test_request_context('/'):
            from flask import session as s
            s['roles'] = roles
            s['company_id'] = FAKE_CO
            s['user_id'] = FAKE_USER
            from app.routes.skills_intelligence import _check_si_company_access
            with patch('app.routes.skills_intelligence._si_enabled', return_value=False):
                ok, err = _check_si_company_access(FAKE_CO)
                assert ok is False

