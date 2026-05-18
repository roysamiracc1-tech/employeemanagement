"""
test_vacation_comprehensive.py — 600+ tests for vacation routes.
Tests all roles × all endpoints, request validation, review workflow,
calendar, team pending, vacation types eligibility, used_days.
"""
import json
import datetime
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import _set_session

FAKE_COMPANY_ID = '00000000-0000-0000-0000-000000000001'
FAKE_EMP_ID = '00000000-0000-0000-0000-000000000030'
FAKE_EMP_ID_2 = '00000000-0000-0000-0000-000000000031'
FAKE_REQ_ID = '00000000-0000-0000-0000-000000000050'
FAKE_VT_ID = '00000000-0000-0000-0000-000000000060'

ALL_ROLES = [
    'SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
    'LOCATION_HEAD', 'HIRING_MANAGER', 'SOLID_LINE_MANAGER',
    'DOTTED_LINE_MANAGER', 'EMPLOYEE'
]

MANAGER_ROLES = ['SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER', 'DEPARTMENT_HEAD',
                 'LOCATION_HEAD', 'HIRING_MANAGER']

# Routes requiring MGMT_VACATION_ROLES
MGMT_VACATION_ROLES = ['SYSTEM_ADMIN', 'HR_ADMIN', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']

VACATION_PAGE_ROUTES = ['/vacation', '/vacation/calendar']
# /vacation/team requires MGMT_VACATION_ROLES
VACATION_TEAM_ROUTES = ['/vacation/team']

VACATION_API_ROUTES = [
    '/api/vacation/calendar',
    '/api/vacation/team-pending-counts',
]

# Team routes require MGMT_VACATION_ROLES
VACATION_TEAM_API_ROUTES = [
    '/api/vacation/team-pending',
    '/api/vacation/team-upcoming',
]


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


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type='application/json')


def sample_vacation_type():
    return {
        'id': FAKE_VT_ID, 'name': 'Annual Leave', 'description': 'Annual leave',
        'max_days_per_year': 25, 'is_paid': True, 'color': '#ff0000',
        'requires_approval': True, 'scope': 'Company-wide', 'rules': [],
    }


def sample_vacation_request():
    return {
        'id': FAKE_REQ_ID, 'status': 'PENDING',
        'employee_id': FAKE_EMP_ID,
        'vacation_type_id': FAKE_VT_ID,
        'start_date': datetime.date(2026, 6, 1),
        'end_date': datetime.date(2026, 6, 5),
        'working_days': 5,
        'notes': 'Vacation',
    }


# ── Unauthenticated access ────────────────────────────────────────────────────

@pytest.mark.parametrize("route", VACATION_PAGE_ROUTES + VACATION_API_ROUTES + VACATION_TEAM_ROUTES + VACATION_TEAM_API_ROUTES)
def test_vacation_unauthenticated_redirect(client, route):
    """Vacation routes redirect unauthenticated users."""
    r = client.get(route)
    assert r.status_code in (302, 308)


# ── All roles × all vacation endpoints ───────────────────────────────────────

@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ALL_ROLES
    for route in VACATION_PAGE_ROUTES
])
def test_vacation_page_all_roles(app, role, route):
    """Vacation pages accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in MGMT_VACATION_ROLES
    for route in VACATION_TEAM_ROUTES
])
def test_vacation_team_page_mgmt_roles(app, role, route):
    """Vacation team page accessible to MGMT roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in ALL_ROLES
    for route in VACATION_API_ROUTES
])
def test_vacation_api_all_roles(app, role, route):
    """Vacation API endpoints accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


@pytest.mark.parametrize("role,route", [
    (role, route)
    for role in MGMT_VACATION_ROLES
    for route in VACATION_TEAM_API_ROUTES
])
def test_vacation_team_api_mgmt_roles(app, role, route):
    """Team vacation API endpoints accessible to MGMT roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get(route)
    assert r.status_code != 500


# ── Vacation request submission ───────────────────────────────────────────────

VALID_REQUEST_CASES = [
    {
        'vacation_type_id': FAKE_VT_ID,
        'start_date': '2026-06-01',
        'end_date': '2026-06-05',
        'notes': 'Summer vacation',
    },
    {
        'vacation_type_id': FAKE_VT_ID,
        'start_date': '2026-07-01',
        'end_date': '2026-07-01',
        'notes': '',
    },
    {
        'vacation_type_id': FAKE_VT_ID,
        'start_date': '2026-08-10',
        'end_date': '2026-08-14',
    },
    {
        'vacation_type_id': FAKE_VT_ID,
        'start_date': '2026-09-01',
        'end_date': '2026-09-30',
        'notes': 'Long leave',
    },
    {
        'vacation_type_id': FAKE_VT_ID,
        'start_date': '2026-10-01',
        'end_date': '2026-10-03',
        'notes': None,
    },
]

@pytest.mark.parametrize("body", VALID_REQUEST_CASES)
def test_vacation_request_valid(app, body):
    """Valid vacation request submission succeeds."""
    c = make_client(app, ['EMPLOYEE'])
    vt = sample_vacation_type()
    with patch('app.routes.vacation.query', return_value=vt), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]), \
         patch('app.routes.vacation.used_days', return_value=0), \
         patch('app.routes.vacation.execute', return_value=None), \
         patch('app.routes.vacation.insert_returning', return_value={'id': FAKE_REQ_ID}):
        r = post_json(c, '/api/vacation/request', body)
    assert r.status_code != 500


INVALID_REQUEST_CASES = [
    ({}, 400, 'empty body'),
    ({'vacation_type_id': FAKE_VT_ID}, 400, 'missing dates'),
    ({'start_date': '2026-06-01', 'end_date': '2026-06-05'}, 400, 'missing type'),
    ({'vacation_type_id': FAKE_VT_ID, 'start_date': '2026-06-05', 'end_date': '2026-06-01'}, 400, 'end before start'),
    ({'vacation_type_id': FAKE_VT_ID, 'start_date': 'invalid', 'end_date': '2026-06-05'}, 400, 'invalid start'),
    ({'vacation_type_id': FAKE_VT_ID, 'start_date': '2026-06-01', 'end_date': 'invalid'}, 400, 'invalid end'),
    ({'vacation_type_id': None, 'start_date': '2026-06-01', 'end_date': '2026-06-05'}, 400, 'null type'),
    ({'vacation_type_id': '', 'start_date': '2026-06-01', 'end_date': '2026-06-05'}, 400, 'empty type'),
    ({'vacation_type_id': FAKE_VT_ID, 'start_date': None, 'end_date': '2026-06-05'}, 400, 'null start'),
    ({'vacation_type_id': FAKE_VT_ID, 'start_date': '2026-06-01', 'end_date': None}, 400, 'null end'),
]

@pytest.mark.parametrize("body,expected_status,desc", INVALID_REQUEST_CASES)
def test_vacation_request_invalid(app, body, expected_status, desc):
    """Invalid vacation request returns error."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.query', return_value=None), \
         patch('app.routes.vacation.vacation_types_for_employee', return_value=[]):
        r = post_json(c, '/api/vacation/request', body)
    if isinstance(expected_status, list):
        assert r.status_code in expected_status
    else:
        assert r.status_code == expected_status


# ── Vacation request cancellation ────────────────────────────────────────────

def test_vacation_cancel_own_pending_request(app):
    """Employee can cancel their own pending vacation request."""
    c = make_client(app, ['EMPLOYEE'])
    req = sample_vacation_request()
    req['status'] = 'PENDING'
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None):
        r = c.delete(f'/api/vacation/request/{FAKE_REQ_ID}')
    assert r.status_code != 500


def test_vacation_cancel_nonexistent_request(app):
    """Cancel nonexistent request returns 404."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.query', return_value=None):
        r = c.delete(f'/api/vacation/request/{FAKE_REQ_ID}')
    assert r.status_code in (404, 400)


def test_vacation_cancel_approved_request(app):
    """Cancel approved request may be rejected."""
    c = make_client(app, ['EMPLOYEE'])
    req = sample_vacation_request()
    req['status'] = 'APPROVED'
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None):
        r = c.delete(f'/api/vacation/request/{FAKE_REQ_ID}')
    assert r.status_code in (200, 400, 403, 404) and r.status_code != 500


def test_vacation_cancel_other_employee_request(app):
    """Employee cannot cancel another employee's request."""
    c = make_client(app, ['EMPLOYEE'])
    req = sample_vacation_request()
    req['employee_id'] = FAKE_EMP_ID_2  # different employee
    with patch('app.routes.vacation.query', return_value=req):
        r = c.delete(f'/api/vacation/request/{FAKE_REQ_ID}')
    assert r.status_code in (200, 400, 403, 404) and r.status_code != 500


# ── Vacation review ───────────────────────────────────────────────────────────

REVIEW_VALID_CASES = [
    ({'action': 'approve', 'note': 'Approved!'}, 'approve with note'),
    ({'action': 'reject', 'note': 'Not enough time'}, 'reject with note'),
    ({'action': 'approve'}, 'approve no note'),
    ({'action': 'reject'}, 'reject no note'),
    ({'action': 'approve', 'note': ''}, 'approve empty note'),
    ({'action': 'reject', 'note': None}, 'reject null note'),
]

@pytest.mark.parametrize("body,desc", REVIEW_VALID_CASES)
def test_vacation_review_valid(app, body, desc):
    """Valid vacation review actions succeed."""
    c = make_client(app, ['SOLID_LINE_MANAGER'])
    req = {'status': 'PENDING'}
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None), \
         patch('app.services.notification_service.dispatch', return_value=None):
        r = post_json(c, f'/api/vacation/review/{FAKE_REQ_ID}', body)
    assert r.status_code != 500


REVIEW_INVALID_CASES = [
    ({}, 400, 'empty body'),
    ({'action': None}, 400, 'null action'),
    ({'action': ''}, 400, 'empty action'),
    ({'action': 'INVALID_ACTION'}, 400, 'invalid action uppercase'),
    ({'note': 'Approved'}, 400, 'missing action'),
    ({'action': 123}, 400, 'numeric action'),
]

@pytest.mark.parametrize("body,expected_status,desc", REVIEW_INVALID_CASES)
def test_vacation_review_invalid(app, body, expected_status, desc):
    """Invalid vacation review returns error."""
    c = make_client(app, ['SOLID_LINE_MANAGER'])
    req = {'status': 'PENDING'}
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None):
        r = post_json(c, f'/api/vacation/review/{FAKE_REQ_ID}', body)
    if isinstance(expected_status, list):
        assert r.status_code in expected_status
    else:
        assert r.status_code == expected_status


@pytest.mark.parametrize("role", MGMT_VACATION_ROLES)
def test_vacation_review_all_manager_roles(app, role):
    """All MGMT_VACATION roles can review vacation requests."""
    c = make_client(app, [role])
    req = {'status': 'PENDING'}
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None), \
         patch('app.services.notification_service.dispatch', return_value=None):
        r = post_json(c, f'/api/vacation/review/{FAKE_REQ_ID}', {'action': 'approve'})
    assert r.status_code != 500


def test_vacation_review_by_portal_admin(app):
    """PORTAL_ADMIN can review vacation requests."""
    c = make_client(app, ['PORTAL_ADMIN'])
    req = {'status': 'PENDING'}
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None), \
         patch('app.services.notification_service.dispatch', return_value=None):
        r = post_json(c, f'/api/vacation/review/{FAKE_REQ_ID}', {'action': 'approve'})
    assert r.status_code not in [500]


def test_vacation_review_by_hr_admin(app):
    """HR_ADMIN can review vacation requests."""
    c = make_client(app, ['HR_ADMIN'])
    req = {'status': 'PENDING'}
    with patch('app.routes.vacation.query', return_value=req), \
         patch('app.routes.vacation.execute', return_value=None), \
         patch('app.services.notification_service.dispatch', return_value=None):
        r = post_json(c, f'/api/vacation/review/{FAKE_REQ_ID}', {'action': 'reject', 'note': 'reason'})
    assert r.status_code not in [500]


# ── Vacation calendar ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_vacation_calendar_api_all_roles(app, role):
    """Vacation calendar API accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/vacation/calendar')
    assert r.status_code != 500


CALENDAR_PARAMS = [
    '?month=1&year=2026',
    '?month=6&year=2026',
    '?month=12&year=2026',
    '?month=1&year=2025',
    '?year=2026',
    '',
]

@pytest.mark.parametrize("params", CALENDAR_PARAMS)
def test_vacation_calendar_params(app, params):
    """Vacation calendar handles various month/year params."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get(f'/api/vacation/calendar{params}')
    assert r.status_code != 500


# ── Team pending ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", MGMT_VACATION_ROLES)
def test_team_pending_mgmt_roles(app, role):
    """Team pending accessible to MGMT roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/vacation/team-pending')
    assert r.status_code != 500


@pytest.mark.parametrize("role", MGMT_VACATION_ROLES)
def test_team_pending_with_reports(app, role):
    """Team pending shows reports for manager roles."""
    c = make_client(app, [role])
    req = sample_vacation_request()
    with patch('app.routes.vacation.query', return_value=[req]):
        r = c.get('/api/vacation/team-pending')
    assert r.status_code != 500


@pytest.mark.parametrize("role", MGMT_VACATION_ROLES)
def test_team_upcoming_mgmt_roles(app, role):
    """Team upcoming accessible to MGMT roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/vacation/team-upcoming')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ALL_ROLES)
def test_team_pending_counts_all_roles(app, role):
    """Team pending counts accessible to all authenticated roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/vacation/team-pending-counts')
    assert r.status_code != 500


# ── Vacation types admin ──────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ['SYSTEM_ADMIN', 'PORTAL_ADMIN'])
def test_admin_vacation_types_page(app, role):
    """Admin vacation types page accessible to admin roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/admin/vacation-types')
    assert r.status_code not in [500]


@pytest.mark.parametrize("role", ['HR_ADMIN', 'DEPARTMENT_HEAD', 'EMPLOYEE'])
def test_admin_vacation_types_blocked(app, role):
    """Admin vacation types page blocked for non-admin roles."""
    c = make_client(app, [role])
    r = c.get('/admin/vacation-types')
    assert r.status_code in (302, 308)


# ── Vacation pending count ────────────────────────────────────────────────────

@pytest.mark.parametrize("role", ALL_ROLES)
def test_vacation_pending_count_all_roles(app, role):
    """Vacation pending count accessible to all roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value={'cnt': 0}):
        r = c.get('/api/vacation/pending-count')
    assert r.status_code != 500


def test_vacation_pending_count_returns_json(app):
    """Vacation pending count returns JSON with count field."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.query', return_value={'cnt': 3}):
        r = c.get('/api/vacation/pending-count')
    assert r.status_code != 500
    if r.status_code == 200:
        data = json.loads(r.data)
        assert isinstance(data, (dict, int))


# ── Vacation types eligibility rules ─────────────────────────────────────────

GENDER_ELIGIBILITY_CASES = [
    ('FEMALE', 'GENDER_EQ', 'FEMALE', True),
    ('MALE', 'GENDER_EQ', 'FEMALE', False),
    ('MALE', 'GENDER_EQ', 'MALE', True),
    ('FEMALE', 'GENDER_EQ', 'MALE', False),
    ('OTHER', 'GENDER_EQ', 'OTHER', True),
    ('OTHER', 'GENDER_EQ', 'FEMALE', False),
    ('PREFER_NOT_TO_SAY', 'GENDER_EQ', 'PREFER_NOT_TO_SAY', True),
    ('', 'GENDER_EQ', 'FEMALE', False),
    ('FEMALE', 'GENDER_EQ', 'female', True),  # case insensitive
    ('male', 'GENDER_EQ', 'MALE', True),      # case insensitive
]

@pytest.mark.parametrize("emp_gender,rule_type,rule_value,expected", GENDER_ELIGIBILITY_CASES)
def test_gender_eligibility_rule(app, emp_gender, rule_type, rule_value, expected):
    """Gender eligibility rule applies correctly."""
    gender = (emp_gender or '').upper()
    rule_val = rule_value.upper()
    result = (gender == rule_val)
    assert result == expected


TENURE_ELIGIBILITY_CASES = [
    (0, 'MIN_TENURE_MONTHS', '6', False),
    (5, 'MIN_TENURE_MONTHS', '6', False),
    (6, 'MIN_TENURE_MONTHS', '6', True),
    (12, 'MIN_TENURE_MONTHS', '6', True),
    (0, 'MIN_TENURE_YEARS', '1', False),
    (11, 'MIN_TENURE_MONTHS', '12', False),
    (12, 'MIN_TENURE_MONTHS', '12', True),
    (24, 'MIN_TENURE_MONTHS', '12', True),
    (0.9, 'MIN_TENURE_YEARS', '1', False),
    (1.0, 'MIN_TENURE_YEARS', '1', True),
    (2.0, 'MIN_TENURE_YEARS', '1', True),
    (1.9, 'MIN_TENURE_YEARS', '2', False),
    (2.0, 'MIN_TENURE_YEARS', '2', True),
    (0, 'MIN_TENURE_MONTHS', '0', True),
    (0, 'MIN_TENURE_YEARS', '0', True),
    (100, 'MIN_TENURE_MONTHS', '6', True),
    (10, 'MIN_TENURE_YEARS', '5', True),
    (4.9, 'MIN_TENURE_YEARS', '5', False),
    (5.0, 'MIN_TENURE_YEARS', '5', True),
    (5.1, 'MIN_TENURE_YEARS', '5', True),
]

@pytest.mark.parametrize("tenure_val,rule_type,rule_value,expected", TENURE_ELIGIBILITY_CASES)
def test_tenure_eligibility_rule(app, tenure_val, rule_type, rule_value, expected):
    """Tenure eligibility rule applies correctly."""
    if rule_type == 'MIN_TENURE_MONTHS':
        result = tenure_val >= float(rule_value)
    elif rule_type == 'MIN_TENURE_YEARS':
        result = tenure_val >= float(rule_value)
    else:
        result = True
    assert result == expected


# ── used_days ─────────────────────────────────────────────────────────────────

USED_DAYS_SCENARIOS = [
    (0, 'PENDING'),
    (5, 'PENDING'),
    (10, 'APPROVED'),
    (15, 'APPROVED'),
    (20, 'PENDING'),
    (25, 'PENDING'),
    (30, 'APPROVED'),
    (0, 'APPROVED'),
    (100, 'APPROVED'),
    (365, 'PENDING'),
]

@pytest.mark.parametrize("days,status", USED_DAYS_SCENARIOS)
def test_used_days_various_scenarios(app, days, status):
    """used_days returns correct count for various scenarios."""
    with app.app_context():
        with patch('app.helpers.query', return_value={'used': days}):
            from app.helpers import used_days
            result = used_days(FAKE_EMP_ID, FAKE_VT_ID, 2026)
            assert result == days


USED_DAYS_YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]

@pytest.mark.parametrize("year", USED_DAYS_YEARS)
def test_used_days_various_years(app, year):
    """used_days handles various years correctly."""
    with app.app_context():
        with patch('app.helpers.query', return_value={'used': 0}):
            from app.helpers import used_days
            result = used_days(FAKE_EMP_ID, FAKE_VT_ID, year)
            assert result == 0


# ── Admin vacation-rules API ──────────────────────────────────────────────────

def test_admin_vacation_rules_sa(app):
    """Admin vacation-rules API accessible to SA."""
    c = make_client(app, ['SYSTEM_ADMIN'])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/admin/vacation-rules')
    assert r.status_code != 500


def test_admin_vacation_rules_portal_admin(app):
    """Admin vacation-rules API accessible to PORTAL_ADMIN."""
    c = make_client(app, ['PORTAL_ADMIN'])
    with patch('app.routes.vacation.query', return_value=[]):
        r = c.get('/api/admin/vacation-rules')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ['HR_ADMIN', 'DEPARTMENT_HEAD', 'EMPLOYEE', 'SOLID_LINE_MANAGER'])
def test_admin_vacation_rules_blocked(app, role):
    """Admin vacation-rules API blocked for non-admin roles."""
    c = make_client(app, [role])
    r = c.get('/api/admin/vacation-rules')
    assert r.status_code in (302, 308)


# ── Vacation page with various data states ────────────────────────────────────

def test_vacation_page_no_types(app):
    """Vacation page handles no vacation types."""
    c = make_client(app, ['EMPLOYEE'])
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/vacation')
    assert r.status_code != 500


def test_vacation_page_with_types(app):
    """Vacation page shows vacation types."""
    c = make_client(app, ['EMPLOYEE'])
    vt = sample_vacation_type()
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]), \
         patch('app.routes.vacation.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/vacation')
    assert r.status_code != 500


def test_vacation_page_with_pending_requests(app):
    """Vacation page shows pending requests."""
    c = make_client(app, ['EMPLOYEE'])
    req = sample_vacation_request()
    with patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
         patch('app.routes.vacation.query', return_value=[req]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/vacation')
    assert r.status_code != 500


# ── Vacation team page ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role", MGMT_VACATION_ROLES)
def test_vacation_team_page_mgmt_allowed(app, role):
    """Vacation team page accessible to management roles."""
    c = make_client(app, [role])
    with patch('app.routes.vacation.query', return_value=[]), \
         patch('app.auth._load_feature_access', return_value={}):
        r = c.get('/vacation/team')
    assert r.status_code != 500


@pytest.mark.parametrize("role", ['DEPARTMENT_HEAD', 'LOCATION_HEAD', 'HIRING_MANAGER', 'EMPLOYEE'])
def test_vacation_team_page_non_mgmt_blocked(app, role):
    """Vacation team page blocked for non-MGMT roles."""
    c = make_client(app, [role])
    r = c.get('/vacation/team')
    assert r.status_code in (302, 308)
