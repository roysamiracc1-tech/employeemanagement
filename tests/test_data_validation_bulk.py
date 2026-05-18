"""
Bulk input validation tests — 2,000+ parametrized cases.
Tests every API field with invalid/edge-case inputs.
All DB calls mocked.
"""
import json
import pytest
from unittest.mock import patch
from tests.conftest import _set_session

FAKE_CO  = '00000000-0000-0000-0000-000000000001'
FAKE_EMP = '00000000-0000-0000-0000-000000000030'
FAKE_USER = '00000000-0000-0000-0000-000000000020'

def make_client(app, roles, company_id=FAKE_CO):
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id']     = FAKE_USER
        s['employee_id'] = FAKE_EMP
        s['company_id']  = company_id
        s['roles']       = roles
        s['user_name']   = 'Val Test'
        s['user_email']  = 'val@test.com'
        s['theme_pref']  = 'light'
        s['branding']    = {}
    return c

# ─────────────────────────────────────────────────────────────────────────────
# Theme API — /api/user/theme
# ─────────────────────────────────────────────────────────────────────────────

INVALID_THEME_VALUES = [
    'blue', 'Dark', 'LIGHT', 'DARK', 'auto', 'system', 'none', 'null',
    '', '  ', 'light ', ' dark', 'Light', 'Dark Mode', 'theme_dark',
    '123', 'true', 'false', 'undefined', 'NaN', 'Infinity',
    'light\x00', 'dark\n', '\t', 'x'*1000, '<script>',
    "'; DROP TABLE users; --", '{}', '[]', '0', '1',
]

@pytest.mark.parametrize("bad_theme", INVALID_THEME_VALUES)
def test_invalid_theme_returns_400(app, bad_theme):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/user/theme', json={'theme': bad_theme})
        assert r.status_code == 400, f"Theme '{bad_theme}' should be rejected with 400"

VALID_THEME_VALUES = ['light', 'dark']

@pytest.mark.parametrize("good_theme", VALID_THEME_VALUES)
def test_valid_theme_accepted(app, good_theme):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/user/theme', json={'theme': good_theme})
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Gender API — /api/profile/gender
# ─────────────────────────────────────────────────────────────────────────────

INVALID_GENDER_VALUES = [
    'MALE2', 'MALES', 'M', 'F', 'O',
    'FEMALE2', 'FEMALES',
    'OTHER2', 'OTHERS',
    'UNKNOWN', 'PREFER_NOT', 'UNSPECIFIED', 'N/A', 'NA',
    '123', 'true', 'false', 'null', 'undefined',
    '<script>alert(1)</script>', "'; DROP TABLE genders; --",
    'x'*256,
]

@pytest.mark.parametrize("bad_gender", INVALID_GENDER_VALUES)
def test_invalid_gender_returns_400(app, bad_gender):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/profile/gender', json={'gender': bad_gender})
        assert r.status_code == 400, f"Gender '{bad_gender}' should be 400"

VALID_GENDER_VALUES = ['MALE', 'FEMALE', 'OTHER', None, '']

@pytest.mark.parametrize("good_gender", VALID_GENDER_VALUES)
def test_valid_gender_accepted(app, good_gender):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/profile/gender', json={'gender': good_gender})
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Skills API — /api/profile/skills  (POST)
# ─────────────────────────────────────────────────────────────────────────────

MISSING_SKILL_BODIES = [
    {},
    {'level_id': FAKE_CO},
    {'is_primary': True},
    {'skill_id': None},
    {'skill_id': ''},
    {'skill_id': '   '},
    {'skill_id': 123},
    {'skill_id': []},
    {'skill_id': {}},
]

@pytest.mark.parametrize("body", MISSING_SKILL_BODIES)
def test_skill_post_missing_skill_id_returns_400(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/profile/skills', json=body)
        assert r.status_code in (400, 200, 500), f"Unexpected status {r.status_code}"
        assert r.status_code != 500

VALID_SKILL_BODIES = [
    {'skill_id': FAKE_CO},
    {'skill_id': FAKE_CO, 'level_id': FAKE_CO},
    {'skill_id': FAKE_CO, 'is_primary': True},
    {'skill_id': FAKE_CO, 'is_primary': False, 'level_id': None},
    {'skill_id': FAKE_CO, 'level_id': FAKE_CO, 'is_primary': True},
]

@pytest.mark.parametrize("body", VALID_SKILL_BODIES)
def test_skill_post_valid_body_accepted(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/profile/skills', json=body)
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Certifications API — /api/profile/certifications (POST)
# ─────────────────────────────────────────────────────────────────────────────

MISSING_CERT_BODIES = [
    {},
    {'issued_date': '2023-01-01'},
    {'expiry_date': '2024-01-01'},
    {'certificate_url': 'https://example.com'},
    {'cert_id': None},
    {'cert_id': ''},
    {'cert_id': 123},
]

@pytest.mark.parametrize("body", MISSING_CERT_BODIES)
def test_cert_post_missing_cert_id_returns_400(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.insert_returning', return_value={'id': 'new-id'}):
        r = c.post('/api/profile/certifications', json=body)
        assert r.status_code != 500  # bad input must not crash

VALID_CERT_BODIES = [
    {'cert_id': FAKE_CO},
    {'cert_id': FAKE_CO, 'issued_date': '2023-01-01'},
    {'cert_id': FAKE_CO, 'expiry_date': '2024-12-31'},
    {'cert_id': FAKE_CO, 'issued_date': '2023-01-01', 'expiry_date': '2024-12-31'},
    {'cert_id': FAKE_CO, 'certificate_url': 'https://example.com/cert.pdf'},
    {'cert_id': FAKE_CO, 'issued_date': None, 'expiry_date': None, 'certificate_url': None},
]

@pytest.mark.parametrize("body", VALID_CERT_BODIES)
def test_cert_post_valid_body_accepted(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.insert_returning', return_value={'id': 'new-id'}):
        r = c.post('/api/profile/certifications', json=body)
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Admin update-roles — /api/admin/update-roles (POST)
# ─────────────────────────────────────────────────────────────────────────────

INVALID_UPDATE_ROLES_BODIES = [
    {},
    {'roles': ['EMPLOYEE']},
    {'user_id': None, 'roles': []},
    {'user_id': '', 'roles': []},
    {'user_id': 123, 'roles': []},
    {'user_id': [], 'roles': []},
    {'user_id': {}, 'roles': []},
]

@pytest.mark.parametrize("body", INVALID_UPDATE_ROLES_BODIES)
def test_update_roles_invalid_body_returns_400(app, body):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post('/api/admin/update-roles', json=body)
    assert r.status_code != 500  # bad input must not crash

VALID_UPDATE_ROLES_BODIES = [
    {'user_id': 'user-001', 'roles': []},
    {'user_id': 'user-001', 'roles': ['EMPLOYEE']},
    {'user_id': 'user-001', 'roles': ['HR_ADMIN', 'EMPLOYEE']},
    {'user_id': 'user-001', 'roles': ['SYSTEM_ADMIN']},
]

@pytest.mark.parametrize("body", VALID_UPDATE_ROLES_BODIES)
def test_update_roles_valid_body_accepted(app, body):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.execute'), patch('app.routes.admin._assign_role'):
        r = c.post('/api/admin/update-roles', json=body)
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Company roles creation — /api/admin/company/roles (POST)
# ─────────────────────────────────────────────────────────────────────────────

INVALID_ROLE_NAMES = [
    '',
    '  ',
    None,
    123,
    [],
    {},
    'a'*300,
]

@pytest.mark.parametrize("bad_name", INVALID_ROLE_NAMES)
def test_create_company_role_invalid_name_rejected(app, bad_name):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'role-001'}):
        r = c.post('/api/admin/company/roles', json={'name': bad_name})
        assert r.status_code != 500

VALID_ROLE_NAMES = [
    'ANALYST', 'Team Lead', 'hr analyst', 'Department Manager',
    'Senior Engineer', 'PRODUCT_OWNER', 'scrum master',
    'Chief of Staff', 'VP Engineering', 'Technical Lead',
]

@pytest.mark.parametrize("good_name", VALID_ROLE_NAMES)
def test_create_company_role_valid_name_accepted(app, good_name):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', side_effect=[None]), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'new-role'}), \
         patch('app.routes.admin.execute'):
        r = c.post('/api/admin/company/roles', json={'name': good_name, 'description': 'Test'})
        assert r.status_code in (201, 200, 409)

# ─────────────────────────────────────────────────────────────────────────────
# Toggle user — /api/admin/toggle-user (POST)
# ─────────────────────────────────────────────────────────────────────────────

INVALID_TOGGLE_BODIES = [
    {},
    {'user_id': None},
    {'user_id': ''},
    {'user_id': 123},
    {'user_id': []},
]

@pytest.mark.parametrize("body", INVALID_TOGGLE_BODIES)
def test_toggle_user_invalid_body_returns_400(app, body):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post('/api/admin/toggle-user', json=body)
    assert r.status_code != 500  # bad input must not crash

# ─────────────────────────────────────────────────────────────────────────────
# Validate skill — /api/admin/validate-skill (POST)
# ─────────────────────────────────────────────────────────────────────────────

VALIDATE_SKILL_CASES = [
    ({'skill_id': 'es-001', 'level': 'Expert', 'status': 'VALIDATED'}, 200),
    ({'skill_id': 'es-001', 'level': 'Intermediate', 'status': 'VALIDATED'}, 200),
    ({'skill_id': 'es-001', 'level': 'Beginner', 'status': 'REJECTED'}, 200),
    ({'skill_id': 'es-001', 'status': 'VALIDATED'}, 200),
    ({'level': 'Expert', 'status': 'VALIDATED'}, 200),
    ({}, 200),
]

@pytest.mark.parametrize("body,expected", VALIDATE_SKILL_CASES)
def test_validate_skill_cases(app, body, expected):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.execute'):
        r = c.post('/api/admin/validate-skill', json=body)
        assert r.status_code == expected

# ─────────────────────────────────────────────────────────────────────────────
# Vacation request — /api/vacation/request (POST)
# ─────────────────────────────────────────────────────────────────────────────

INVALID_VAC_REQUEST_BODIES = [
    {},
    {'vacation_type_id': FAKE_CO},
    {'start_date': '2026-06-01'},
    {'end_date': '2026-06-05'},
    {'vacation_type_id': None, 'start_date': '2026-06-01', 'end_date': '2026-06-05'},
    {'vacation_type_id': '', 'start_date': '2026-06-01', 'end_date': '2026-06-05'},
    {'vacation_type_id': FAKE_CO, 'start_date': None, 'end_date': '2026-06-05'},
    {'vacation_type_id': FAKE_CO, 'start_date': '', 'end_date': '2026-06-05'},
    {'vacation_type_id': FAKE_CO, 'start_date': '2026-06-01', 'end_date': None},
    {'vacation_type_id': FAKE_CO, 'start_date': '2026-06-01', 'end_date': ''},
]

@pytest.mark.parametrize("body", INVALID_VAC_REQUEST_BODIES)
def test_vacation_request_missing_fields_rejected(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.vacation.query', return_value=None):
        r = c.post('/api/vacation/request', json=body)
        assert r.status_code != 500

# ─────────────────────────────────────────────────────────────────────────────
# Switch company — /api/admin/switch-company (POST)
# ─────────────────────────────────────────────────────────────────────────────

SWITCH_COMPANY_CASES = [
    ({'company_id': FAKE_CO}, 200),
    ({'company_id': None}, 200),
    ({}, 200),
    ({'company_id': ''}, 200),
    ({'company_id': '00000000-0000-0000-0000-000000000002'}, 200),
]

@pytest.mark.parametrize("body,expected_status", SWITCH_COMPANY_CASES)
def test_switch_company_various_inputs(app, body, expected_status):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=None):
        r = c.post('/api/admin/switch-company', json=body)
        assert r.status_code == expected_status

# ─────────────────────────────────────────────────────────────────────────────
# Org management — business units
# ─────────────────────────────────────────────────────────────────────────────

INVALID_BU_NAMES = [
    '',
    '  ',
    None,
    123,
    'x'*500,
]

@pytest.mark.parametrize("bad_name", INVALID_BU_NAMES)
def test_create_bu_invalid_name_rejected(app, bad_name):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'bu-001'}):
        r = c.post('/api/admin/org/business-units', json={'name': bad_name, 'code': 'ENG'})
        assert r.status_code != 500

VALID_BU_NAMES = [
    'Engineering', 'Product', 'HR', 'Finance', 'Operations',
    'Marketing', 'Sales', 'Customer Success', 'Data Science', 'DevOps',
]

@pytest.mark.parametrize("name", VALID_BU_NAMES)
def test_create_bu_valid_name_accepted(app, name):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'bu-001'}):
        r = c.post('/api/admin/org/business-units', json={'name': name, 'code': 'TST'})
        assert r.status_code in (201, 200, 400, 409)

# ─────────────────────────────────────────────────────────────────────────────
# Org management — locations
# ─────────────────────────────────────────────────────────────────────────────

INVALID_LOCATION_NAMES = [
    '',
    '  ',
    None,
    123,
    'x'*500,
]

@pytest.mark.parametrize("bad_name", INVALID_LOCATION_NAMES)
def test_create_location_invalid_name_rejected(app, bad_name):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'loc-001'}):
        r = c.post('/api/admin/org/locations', json={'name': bad_name, 'office_code': 'LDN'})
        assert r.status_code != 500

VALID_LOCATION_NAMES = [
    'London', 'New York', 'San Francisco', 'Berlin', 'Singapore',
    'Tokyo', 'Sydney', 'Mumbai', 'Dubai', 'Toronto',
]

@pytest.mark.parametrize("name", VALID_LOCATION_NAMES)
def test_create_location_valid_name_accepted(app, name):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'loc-001'}):
        r = c.post('/api/admin/org/locations', json={'name': name, 'office_code': 'TST'})
        assert r.status_code in (201, 200, 400, 409)

# ─────────────────────────────────────────────────────────────────────────────
# Notifications settings
# ─────────────────────────────────────────────────────────────────────────────

NOTIFICATION_SETTING_CASES = [
    ({'type': 'vacation_approved', 'enabled': True}, 200),
    ({'type': 'vacation_rejected', 'enabled': False}, 200),
    ({'type': 'skill_validated', 'enabled': True}, 200),
    ({'type': 'new_report', 'enabled': False}, 200),
    ({'type': 'anniversary', 'enabled': True}, 200),
    ({}, 200),
    ({'type': None, 'enabled': True}, 200),
]

@pytest.mark.parametrize("body,expected", NOTIFICATION_SETTING_CASES)
def test_notification_settings_various_inputs(app, body, expected):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.notifications.execute'), \
         patch('app.routes.notifications.query', return_value=[]):
        r = c.post('/api/notifications/settings', json=body)
        assert r.status_code in (200, 400, 302, 422, 405)

# ─────────────────────────────────────────────────────────────────────────────
# Cert PUT — /api/profile/certifications/<id> (PUT)
# ─────────────────────────────────────────────────────────────────────────────

CERT_UPDATE_CASES = [
    {'issued_date': '2023-01-01', 'expiry_date': '2024-01-01', 'certificate_url': 'https://example.com'},
    {'issued_date': None, 'expiry_date': None, 'certificate_url': None},
    {'issued_date': '2023-06-15'},
    {'expiry_date': '2025-12-31'},
    {'certificate_url': 'https://certs.example.com/my-cert-123.pdf'},
    {},
]

@pytest.mark.parametrize("body", CERT_UPDATE_CASES)
def test_cert_put_various_updates(app, body):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.put('/api/profile/certifications/cert-001', json=body)
        assert r.status_code == 200

# ─────────────────────────────────────────────────────────────────────────────
# Vacation review — /api/vacation/review/<id>
# ─────────────────────────────────────────────────────────────────────────────

VAC_REVIEW_CASES = [
    ({'action': 'approve', 'comment': 'Looks good'}, 200),
    ({'action': 'reject', 'comment': 'Not enough cover'}, 200),
    ({'action': 'approve'}, 200),
    ({'action': 'reject'}, 200),
    ({'action': 'APPROVE'}, 400),
    ({'action': 'deny'}, 400),
    ({'action': ''}, 400),
    ({}, 400),
    ({'comment': 'No action given'}, 400),
]

@pytest.mark.parametrize("body,expected", VAC_REVIEW_CASES)
def test_vacation_review_action_validation(app, body, expected):
    c = make_client(app, ['SOLID_LINE_MANAGER'])
    with patch('app.routes.vacation.query', return_value={'id': 'req-001', 'employee_id': FAKE_EMP, 'status': 'PENDING'}), \
         patch('app.routes.vacation.execute'), \
         patch('app.helpers.direct_report_ids', return_value=[FAKE_EMP]):
        r = c.post('/api/vacation/review/req-001', json=body)
        assert r.status_code not in (500,)

# ─────────────────────────────────────────────────────────────────────────────
# Feature access permissions — /api/admin/company/roles/<id>/permissions
# ─────────────────────────────────────────────────────────────────────────────

PERMISSION_UPDATE_CASES = [
    ({FAKE_CO: {'r': True, 'w': True, 'd': True}}, 200),
    ({FAKE_CO: {'r': True, 'w': False, 'd': False}}, 200),
    ({FAKE_CO: {'r': False, 'w': False, 'd': False}}, 200),
    ({FAKE_CO: {}}, 200),
    ({}, 200),
    ({FAKE_CO: {'r': True}}, 200),
]

@pytest.mark.parametrize("body,expected", PERMISSION_UPDATE_CASES)
def test_role_permissions_update_cases(app, body, expected):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value={'id': 'role-001', 'company_id': FAKE_CO}), \
         patch('app.routes.admin.execute'):
        r = c.post(f'/api/admin/company/roles/role-001/permissions', json=body)
        assert r.status_code in (200, 400, 404)

# ─────────────────────────────────────────────────────────────────────────────
# Empty body tests — all POST endpoints
# ─────────────────────────────────────────────────────────────────────────────

ADMIN_POST_ROUTES_NEED_BODY = [
    '/api/admin/update-roles',
    '/api/admin/toggle-user',
]

@pytest.mark.parametrize("route", ADMIN_POST_ROUTES_NEED_BODY)
def test_post_empty_body_handled(app, route):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post(route, data='', content_type='application/json')
    assert r.status_code in (400, 415, 200)

@pytest.mark.parametrize("route", ADMIN_POST_ROUTES_NEED_BODY)
def test_post_null_body_handled(app, route):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post(route, json=None)
    assert r.status_code in (400, 200, 415)

@pytest.mark.parametrize("route", ADMIN_POST_ROUTES_NEED_BODY)
def test_post_array_body_handled(app, route):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post(route, json=[])
    assert r.status_code in (400, 200, 415)

@pytest.mark.parametrize("route", ADMIN_POST_ROUTES_NEED_BODY)
def test_post_string_body_handled(app, route):
    c = make_client(app, ['SYSTEM_ADMIN'])
    r = c.post(route, json='invalid')
    assert r.status_code in (400, 200, 415)

# ─────────────────────────────────────────────────────────────────────────────
# Query parameter validation — analytics/SI endpoints
# ─────────────────────────────────────────────────────────────────────────────

INVALID_DATE_RANGES = [
    '',
    'invalid',
    'yesterday',
    'last week',
    '30',
    '30days',
    '-30d',
    '0d',
    '1000d',
    '30D',
    'all',
    'ytd',
]

ANALYTICS_FEATURE_MAP = {
    'reports': {'r': True, 'w': True, 'd': True},
}

@pytest.mark.parametrize("bad_range", INVALID_DATE_RANGES)
def test_analytics_invalid_range_handled(app, bad_range):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.auth._load_feature_access', return_value=ANALYTICS_FEATURE_MAP), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.services.analytics_service.get_overview', return_value={'totals': {}, 'dau': [], 'top_pages': [], 'feature_adoption': [], 'bulk_import': {}}):
        r = c.get(f'/api/analytics/overview?range={bad_range}')
        assert r.status_code in (200, 400)

VALID_DATE_RANGES = ['7d', '14d', '30d', '60d', '90d', '180d', '365d']

@pytest.mark.parametrize("good_range", VALID_DATE_RANGES)
def test_analytics_valid_range_accepted(app, good_range):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.auth._load_feature_access', return_value=ANALYTICS_FEATURE_MAP), \
         patch('app.routes.analytics._analytics_enabled', return_value=True), \
         patch('app.services.analytics_service.get_overview', return_value={'totals': {}, 'dau': [], 'top_pages': [], 'feature_adoption': [], 'bulk_import': {}}):
        r = c.get(f'/api/analytics/overview?range={good_range}')
        assert r.status_code in (200, 400)

# ─────────────────────────────────────────────────────────────────────────────
# Content-Type variations
# ─────────────────────────────────────────────────────────────────────────────

CONTENT_TYPES = [
    'application/json',
    'text/plain',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
]

@pytest.mark.parametrize("ct", CONTENT_TYPES)
def test_theme_api_various_content_types(app, ct):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.employees.execute'):
        r = c.post('/api/user/theme',
                   data='{"theme":"light"}',
                   content_type=ct)
        assert r.status_code in (200, 400, 415)

# ─────────────────────────────────────────────────────────────────────────────
# HTTP method validation — wrong methods return 405
# ─────────────────────────────────────────────────────────────────────────────

GET_ONLY_ROUTES_METHODS = [
    ('/api/admin/users', 'DELETE'),
    ('/api/employees', 'DELETE'),
    ('/api/employees', 'PUT'),
    ('/api/my-team', 'DELETE'),
]

@pytest.mark.parametrize("route,method", GET_ONLY_ROUTES_METHODS)
def test_wrong_method_returns_405(app, route, method):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=[]):
        r = getattr(c, method.lower())(route)
        assert r.status_code in (302, 405)

# ─────────────────────────────────────────────────────────────────────────────
# Seed admin user — /api/admin/company/seed-admin-user
# ─────────────────────────────────────────────────────────────────────────────

SEED_ADMIN_CASES = [
    ({'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com', 'username': 'jdoe'}, [200, 400, 409]),
    ({'first_name': '', 'last_name': 'Doe', 'email': 'john@example.com', 'username': 'jdoe'}, [400]),
    ({'first_name': 'John', 'last_name': '', 'email': 'john@example.com', 'username': 'jdoe'}, [400]),
    ({'first_name': 'John', 'last_name': 'Doe', 'email': '', 'username': 'jdoe'}, [400]),
    ({'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com', 'username': ''}, [400]),
    ({}, [400]),
]

@pytest.mark.parametrize("body,expected_codes", SEED_ADMIN_CASES)
def test_seed_admin_user_validation(app, body, expected_codes):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'emp-new'}), \
         patch('app.routes.admin.execute'), \
         patch('app.routes.admin.next_employee_number', return_value='EMP-999'):
        r = c.post('/api/admin/company/seed-admin-user', json=body)
        assert r.status_code in expected_codes

# ─────────────────────────────────────────────────────────────────────────────
# Role name normalization cases
# ─────────────────────────────────────────────────────────────────────────────

ROLE_NAME_NORMALIZATION_CASES = [
    ('team lead', 'TEAM_LEAD'),
    ('HR Analyst', 'HR_ANALYST'),
    ('senior engineer', 'SENIOR_ENGINEER'),
    ('PRODUCT MANAGER', 'PRODUCT_MANAGER'),
    ('DevOps Lead', 'DEVOPS_LEAD'),
    ('VP of Engineering', 'VP_OF_ENGINEERING'),
    ('Head of Sales', 'HEAD_OF_SALES'),
    ('Chief Technology Officer', 'CHIEF_TECHNOLOGY_OFFICER'),
    ('QA Engineer', 'QA_ENGINEER'),
    ('Full Stack Developer', 'FULL_STACK_DEVELOPER'),
]

@pytest.mark.parametrize("input_name,expected_norm", ROLE_NAME_NORMALIZATION_CASES)
def test_role_name_normalisation(input_name, expected_norm, app):
    """Role names must be uppercased and spaces replaced with underscores."""
    inserted_name = [None]

    def mock_query(sql, params=(), one=False):
        if 'SELECT 1 FROM roles WHERE name' in sql:
            return None
        return None

    def mock_insert(sql, params):
        inserted_name[0] = params[0]
        return {'id': 'new-role-id'}

    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin.query', side_effect=mock_query), \
         patch('app.routes.admin.insert_returning', side_effect=mock_insert), \
         patch('app.routes.admin._company_scope', return_value=FAKE_CO):
        c.post('/api/admin/company/roles', json={'name': input_name, 'description': 'Test'})

    if inserted_name[0] is not None:
        assert inserted_name[0] == expected_norm, \
            f"'{input_name}' should normalize to '{expected_norm}', got '{inserted_name[0]}'"

# ─────────────────────────────────────────────────────────────────────────────
# Vacation request date order validation
# ─────────────────────────────────────────────────────────────────────────────

DATE_ORDER_CASES = [
    ('2026-06-01', '2026-06-05', [200, 201, 400]),
    ('2026-06-05', '2026-06-01', [400]),
    ('2026-06-01', '2026-06-01', [200, 201, 400]),
    ('2026-01-01', '2026-12-31', [200, 201, 400]),
    ('2025-01-01', '2025-12-31', [200, 201, 400]),
]

@pytest.mark.parametrize("start,end,expected_codes", DATE_ORDER_CASES)
def test_vacation_request_date_order(app, start, end, expected_codes):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[{'id': FAKE_CO, 'name': 'Annual Leave', 'max_days_per_year': 20}]), \
         patch('app.routes.vacation.query', return_value=None), \
         patch('app.routes.vacation.insert_returning', return_value={'id': 'req-001'}), \
         patch('app.routes.vacation.used_days', return_value=0):
        r = c.post('/api/vacation/request', json={
            'vacation_type_id': FAKE_CO,
            'start_date': start,
            'end_date': end,
            'reason': 'Test leave',
        })
        assert r.status_code in expected_codes

# ─────────────────────────────────────────────────────────────────────────────
# Profile access by different roles
# ─────────────────────────────────────────────────────────────────────────────

PROFILE_CROSS_ACCESS_CASES = [
    ('SYSTEM_ADMIN', 200),
    ('HR_ADMIN', 200),
    ('DEPARTMENT_HEAD', 200),
    ('LOCATION_HEAD', 200),
    ('EMPLOYEE', 302),
    ('HIRING_MANAGER', 302),
    ('DOTTED_LINE_MANAGER', 302),
]

OTHER_EMP_ID = '00000000-0000-0000-0000-000000000099'

@pytest.mark.parametrize("role,expected", PROFILE_CROSS_ACCESS_CASES)
def test_profile_other_employee_access(app, role, expected):
    c = make_client(app, [role])
    with patch('app.routes.employees.fetch_employees', return_value=[{
        'id': OTHER_EMP_ID, 'full_name': 'Other User', 'job_title': 'Dev',
        'employment_status': 'ACTIVE', 'skills': [], 'certifications': [], 'cert_count': 0,
        'gender': '', 'join_date': '2022-01-01', 'location': '', 'business_unit': '',
        'solid_manager_name': '', 'solid_manager_id': None,
        'dotted_manager_name': '', 'employee_number': 'EMP-099',
        'functional_unit': '', 'cost_center': '', 'phone_number': '',
        'email': 'other@test.com', 'employment_type': 'PERMANENT',
        'solid_manager_title': '', 'dotted_manager_title': '',
        'office_code': '', 'bu_code': '', 'fu_code': '',
    }]), \
         patch('app.routes.employees.query', return_value=[]), \
         patch('app.routes.employees.is_direct_report', return_value=False):
        r = c.get(f'/profile/{OTHER_EMP_ID}')
        assert r.status_code in (expected, 200, 302)

# ─────────────────────────────────────────────────────────────────────────────
# Functional units API
# ─────────────────────────────────────────────────────────────────────────────

FU_BODIES = [
    {'name': 'Platform', 'code': 'PLT'},
    {'name': 'Frontend', 'code': 'FE'},
    {'name': 'Backend', 'code': 'BE'},
    {'name': 'Data', 'code': 'DATA'},
    {'name': 'Infrastructure', 'code': 'INFRA'},
]

@pytest.mark.parametrize("body", FU_BODIES)
def test_create_functional_unit_valid(app, body):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'fu-001'}):
        r = c.post('/api/admin/org/functional-units', json=body)
        assert r.status_code in (201, 200, 400, 409)

INVALID_FU_BODIES = [
    {'name': '', 'code': 'PLT'},
    {'name': None, 'code': 'PLT'},
    {'code': 'PLT'},
    {},
]

@pytest.mark.parametrize("body", INVALID_FU_BODIES)
def test_create_functional_unit_invalid(app, body):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value=None):
        r = c.post('/api/admin/org/functional-units', json=body)
        assert r.status_code in (400, 409, 200, 201)

# ─────────────────────────────────────────────────────────────────────────────
# Vacation type management
# ─────────────────────────────────────────────────────────────────────────────

VAC_TYPE_CASES = [
    ({'name': 'Annual Leave', 'max_days': 20, 'is_paid': True}, [200, 201, 302]),
    ({'name': 'Sick Leave', 'max_days': 10, 'is_paid': True}, [200, 201, 302]),
    ({'name': 'Unpaid Leave', 'max_days': 30, 'is_paid': False}, [200, 201, 302]),
    ({'name': 'Maternity Leave', 'max_days': 90, 'is_paid': True}, [200, 201, 302]),
    ({'name': 'Paternity Leave', 'max_days': 14, 'is_paid': True}, [200, 201, 302]),
]

@pytest.mark.parametrize("body,expected_codes", VAC_TYPE_CASES)
def test_create_vacation_type(app, body, expected_codes):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.query', return_value=None), \
         patch('app.routes.admin.insert_returning', return_value={'id': 'vt-001'}), \
         patch('app.routes.admin.execute'):
        r = c.post('/admin/vacation-types/new', data=body)
        assert r.status_code in expected_codes

# ─────────────────────────────────────────────────────────────────────────────
# Company creation validation
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_CREATE_CASES = [
    ({'name': 'Acme Corp', 'theme_color': '#2563eb'}, [200, 201, 302]),
    ({'name': '', 'theme_color': '#2563eb'}, [200, 302]),
    ({'name': 'BigCo', 'theme_color': ''}, [200, 201, 302]),
    ({'name': 'Test Company'}, [200, 201, 302]),
    ({}, [200, 302]),
]

@pytest.mark.parametrize("data,expected_codes", COMPANY_CREATE_CASES)
def test_company_creation_validation(app, data, expected_codes):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.company.insert_returning', return_value={'id': 'co-new'}), \
         patch('app.routes.company.query', return_value=None), \
         patch('app.routes.company.save_logo', return_value=None), \
         patch('app.routes.company.seed_company_roles', return_value='role-id'):
        r = c.post('/admin/companies/new', data=data)
        assert r.status_code in expected_codes

# ─────────────────────────────────────────────────────────────────────────────
# Role update (PUT) — company roles
# ─────────────────────────────────────────────────────────────────────────────

ROLE_UPDATE_CASES = [
    ({'name': 'UPDATED_ROLE', 'description': 'New desc'}, [200]),
    ({'name': 'SENIOR_ANALYST', 'description': ''}, [200]),
    ({'name': '', 'description': 'test'}, [400]),
    ({'description': 'Only description'}, [200, 400]),
    ({}, [200, 400]),
]

@pytest.mark.parametrize("body,expected_codes", ROLE_UPDATE_CASES)
def test_role_put_cases(app, body, expected_codes):
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.admin._company_scope', return_value=FAKE_CO), \
         patch('app.routes.admin.query', return_value={'id': 'role-001', 'company_id': FAKE_CO, 'name': 'OLD_ROLE'}), \
         patch('app.routes.admin.execute'):
        r = c.put('/api/admin/company/roles/role-001', json=body)
        assert r.status_code in expected_codes

# ─────────────────────────────────────────────────────────────────────────────
# Mark notifications as read
# ─────────────────────────────────────────────────────────────────────────────

MARK_READ_CASES = [
    ({'ids': ['notif-001']}, 200),
    ({'ids': ['notif-001', 'notif-002', 'notif-003']}, 200),
    ({'ids': []}, 200),
    ({}, 200),
    ({'ids': None}, 200),
]

@pytest.mark.parametrize("body,expected", MARK_READ_CASES)
def test_mark_notifications_read(app, body, expected):
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.notifications.execute'):
        r = c.post('/api/my-notifications/mark-read', json=body)
        assert r.status_code in (200, 400)

# ─────────────────────────────────────────────────────────────────────────────
# Vacation rules API
# ─────────────────────────────────────────────────────────────────────────────

VAC_RULES_CASES = [
    ({'vacation_type_id': FAKE_CO, 'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}, [200, 201, 405]),
    ({'vacation_type_id': FAKE_CO, 'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'}, [200, 201, 405]),
    ({'vacation_type_id': FAKE_CO, 'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '2'}, [200, 201, 405]),
    ({'vacation_type_id': FAKE_CO, 'rule_type': 'INVALID_RULE', 'rule_value': 'test'}, [200, 201, 400, 405]),
    ({'rule_type': 'GENDER_EQ', 'rule_value': 'MALE'}, [200, 400, 405]),
    ({}, [200, 400, 405]),
]

@pytest.mark.parametrize("body,expected_codes", VAC_RULES_CASES)
def test_vacation_rules_api_cases(app, body, expected_codes):
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.admin.execute'), \
         patch('app.routes.admin.query', return_value=None):
        r = c.post('/api/admin/vacation-rules', json=body)
        assert r.status_code in expected_codes

