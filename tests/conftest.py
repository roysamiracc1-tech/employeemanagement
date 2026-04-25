"""
Shared pytest fixtures.
All DB calls are mocked — no live PostgreSQL required to run tests.
"""
import datetime
import pytest
from unittest.mock import patch, MagicMock

from app import app as flask_app


# ── App / client fixtures ────────────────────────────────────────────────────

@pytest.fixture
def app():
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY='test-secret',
        WTF_CSRF_ENABLED=False,
    )
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ── Helpers for faking a logged-in session ────────────────────────────────────

def _set_session(client, roles=None, employee_id='emp-001', user_id='user-001'):
    with client.session_transaction() as sess:
        sess['user_id']     = user_id
        sess['employee_id'] = employee_id
        sess['user_name']   = 'Test User'
        sess['user_email']  = 'test@example.com'
        sess['user_title']  = 'Developer'
        sess['roles']       = roles or ['EMPLOYEE']
        sess['theme_pref']  = 'light'
        sess['branding']    = {}


@pytest.fixture
def auth_client(client):
    """Client with a standard EMPLOYEE session."""
    _set_session(client)
    return client


@pytest.fixture
def admin_client(client):
    """Client with a SYSTEM_ADMIN session."""
    _set_session(client, roles=['SYSTEM_ADMIN', 'EMPLOYEE'])
    return client


@pytest.fixture
def manager_client(client):
    """Client with a SOLID_LINE_MANAGER session."""
    _set_session(client, roles=['SOLID_LINE_MANAGER', 'EMPLOYEE'])
    return client


# ── Reusable sample data ──────────────────────────────────────────────────────

SAMPLE_EMPLOYEE = {
    'id': 'emp-001',
    'employee_number': 'EMP-001',
    'full_name': 'Jane Smith',
    'first_name': 'Jane',
    'last_name': 'Smith',
    'email': 'jane@example.com',
    'phone_number': '',
    'job_title': 'Engineer',
    'employment_status': 'ACTIVE',
    'employment_type': 'PERMANENT',
    'gender': 'FEMALE',
    'join_date': '2022-01-15',
    'location': 'London',
    'office_code': 'LDN',
    'business_unit': 'Engineering',
    'bu_code': 'ENG',
    'functional_unit': 'Platform',
    'fu_code': 'PLT',
    'cost_center': 'CC-001',
    'solid_manager_name': 'Bob Manager',
    'solid_manager_title': 'Head of Eng',
    'solid_manager_id': 'mgr-001',
    'dotted_manager_name': '',
    'dotted_manager_title': '',
    'skills': [],
    'cert_count': 0,
    'certifications': [],
}

SAMPLE_VACATION_TYPE = {
    'id': 'vt-001',
    'name': 'Annual Leave',
    'description': 'Standard annual leave',
    'max_days_per_year': 20,
    'is_paid': True,
    'color': '#3b82f6',
    'scope': 'Company-wide',
}
