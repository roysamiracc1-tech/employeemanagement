"""
Shared pytest fixtures.
All DB calls are mocked — no live PostgreSQL required to run tests.
"""
import datetime
from contextlib import contextmanager

import pytest
from unittest.mock import patch, MagicMock

from app import app as flask_app


# ── Transaction harness (KAN-155 / ADR-006) ───────────────────────────────────
#
# Service-layer tests mock the DB, so the real `transaction()` — which needs an
# app context and a live connection — has to be stood in for. It lives here
# rather than in one suite because several suites drive the same services, and a
# second copy would drift from ADR-006's rules.

class FakeTransaction:
    """Stand-in for `app.db.transaction()` in DB-mocked service tests.

    Records how many units of work were opened and committed, and refuses to
    nest — so a service that accidentally opens a second transaction inside an
    open one fails here rather than silently creating a false commit boundary.
    """

    def __init__(self):
        self.open = False
        self.opened = 0
        self.committed = 0

    @contextmanager
    def __call__(self):
        assert not self.open, 'transaction() must not be nested (ADR-006)'
        self.open = True
        self.opened += 1
        try:
            yield None
        finally:
            self.open = False
        self.committed += 1


def recording_execute(txn):
    """execute() replacement that also records whether it ran inside `txn`."""
    inside = []

    def _execute(sql, params=()):
        inside.append(bool(txn.open))

    mock = MagicMock(side_effect=_execute)
    mock.inside = inside
    return mock


def assert_single_atomic_unit(txn, exe):
    """Every write went through exactly one committed transaction."""
    assert txn.opened == 1, f'expected one unit of work, saw {txn.opened}'
    assert txn.committed == 1, 'the unit of work did not commit'
    assert exe.inside and all(exe.inside), 'a write ran outside the transaction'


# ── The tenant feature switch (KAN-188) ───────────────────────────────────────
#
# Replaces the per-feature `_si_enabled` / `_analytics_enabled` mocks that tests
# used before KAN-188. Those patched a hand-rolled gate that lived inside two
# route modules; there is now ONE resolver, so a test that wants to say "this
# company does not have this feature" should say exactly that, once, rather than
# reach into whichever module happens to implement it this week.
#
# Both helpers patch `can_access_feature` AND `tenant_feature_state` together,
# because the decorator consults both and they must agree: the first decides
# whether to refuse, the second decides WHICH refusal — the explanatory
# "your company doesn't have this" screen, or the generic "you don't have
# access" flash. Patching only one produces a state the product cannot reach.

def _auth_module():
    """`app.auth`, fetched by full dotted name.

    NOT `from app import auth` — `app/routes/auth.py` also exists and binds
    itself as the `auth` attribute of the `app` package once imported, so the
    plain form silently hands back the routes module and the patch lands on the
    wrong object.
    """
    import importlib
    return importlib.import_module('app.auth')


@contextmanager
def tenant_feature_off(feature_code):
    """The company does NOT have *feature_code*; every other feature is fine.

    **Honours the SYSTEM_ADMIN bypass**, because the real resolver does: a system
    admin administers the switch, so being locked out by it would make a
    mis-toggle unrecoverable through the UI. A helper that ignored that would
    make "SA can still reach it" tests fail against correct code — and, worse,
    would let a real regression in the bypass pass unnoticed.

    `tenant_feature_state` still reports False even for a system admin: the
    switch IS off, and the off-state screen uses exactly that to tell them so
    rather than letting them demo a page nobody else can see.
    """
    from flask import session, has_request_context
    auth = _auth_module()

    def _is_sa():
        return has_request_context() and 'SYSTEM_ADMIN' in (session.get('roles') or [])

    def _access(code, action='r'):
        return True if _is_sa() else code != feature_code

    def _state(code, company_id=None):
        return code != feature_code

    # `_role_grants` answers "would their role allow it if the company had the
    # feature?" — True here, because these tests are about the SWITCH, not the
    # grant. Without it the decorator falls through to the generic denial and
    # the off-state screen is never reached.
    with patch.object(auth, 'can_access_feature', side_effect=_access), \
         patch.object(auth, 'tenant_feature_state', side_effect=_state), \
         patch.object(auth, '_role_grants', return_value=True):
        yield


@contextmanager
def tenant_feature_on(feature_code=None):
    """The company HAS the feature (and the role grant allows it).

    `feature_code` is accepted and ignored — it documents intent at the call
    site. Everything resolves to allowed, which is what the old
    `_si_enabled=True` / `_analytics_enabled=True` mocks meant.
    """
    auth = _auth_module()
    with patch.object(auth, 'can_access_feature', return_value=True), \
         patch.object(auth, 'tenant_feature_state', return_value=True):
        yield


@contextmanager
def tenant_on_role_denied():
    """The company HAS the feature but the user's ROLE does not grant it.

    The other refusal, and it must stay distinguishable from the tenant-off one:
    this is a permissions conversation (redirect + flash), the other is a
    licensing one (explanatory screen). Tests that patch `_load_feature_access`
    to a partial map are asserting THIS case, so they have to pin the tenant
    switch ON — otherwise a fixture company with no `company_features` rows
    reads as tenant-off and the wrong refusal wins, which says nothing about
    the rule under test.
    """
    auth = _auth_module()
    with patch.object(auth, 'tenant_feature_state', return_value=True), \
         patch.object(auth, '_role_grants', return_value=False):
        yield


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
