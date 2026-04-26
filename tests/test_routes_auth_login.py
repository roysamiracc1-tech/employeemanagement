"""
Integration tests for login / logout flows.
All DB calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session


# ── Fixtures ─────────────────────────────────────────────────────────────────

DEMO_USER_ROW = {
    'id': 'user-001', 'employee_id': 'emp-001',
    'email': 'oliver@company.com',
    'first_name': 'Oliver', 'last_name': 'Hartmann',
    'job_title': 'CTO', 'company_id': None,
    'theme_preference': 'light',
    'roles': ['SYSTEM_ADMIN', 'EMPLOYEE'],
}

DEMO_USERS_LIST = [
    {'name': 'Oliver Hartmann', 'email': 'oliver@company.com',
     'job_title': 'CTO', 'roles': ['SYSTEM_ADMIN', 'EMPLOYEE']},
]


# ─────────────────────────────────────────────────────────────────────────────
class TestLoginPage:
    def test_get_returns_200(self, client):
        with patch('app.routes.auth.query', return_value=DEMO_USERS_LIST):
            r = client.get('/login')
        assert r.status_code == 200

    def test_html_contains_form(self, client):
        with patch('app.routes.auth.query', return_value=DEMO_USERS_LIST):
            r = client.get('/login')
        html = r.data.decode()
        assert '<form' in html
        assert 'name="email"' in html

    def test_demo_users_rendered_from_query(self, client):
        with patch('app.routes.auth.query', return_value=DEMO_USERS_LIST):
            r = client.get('/login')
        html = r.data.decode()
        assert 'Oliver Hartmann' in html
        assert 'oliver@company.com' in html

    def test_no_demo_panel_when_no_demo_users(self, client):
        with patch('app.routes.auth.query', return_value=[]):
            r = client.get('/login')
        html = r.data.decode()
        assert 'demo-chip' not in html

    def test_redirects_already_logged_in_user(self, client):
        _set_session(client)
        r = client.get('/login')
        assert r.status_code in (301, 302)
        assert '/dashboard' in r.headers.get('Location', '')

    def test_index_redirects_to_login_when_unauthenticated(self, client):
        r = client.get('/')
        assert r.status_code in (301, 302)
        assert 'login' in r.headers.get('Location', '')

    def test_index_redirects_to_dashboard_when_authenticated(self, client):
        _set_session(client)
        r = client.get('/')
        assert r.status_code in (301, 302)
        assert 'dashboard' in r.headers.get('Location', '')


class TestLoginPost:
    def _mock_login(self, client, email, user_row, brand_row=None):
        def query_side(sql, params=(), one=False):
            if 'LOWER(u.email)' in sql or 'LOWER(e.email)' in sql or 'LOWER' in sql:
                if one:
                    return user_row if user_row else None
                return [user_row] if user_row else []
            if 'companies' in sql:
                return brand_row if one else ([brand_row] if brand_row else [])
            return None if one else []

        with patch('app.routes.auth.query', side_effect=query_side), \
             patch('app.routes.auth.execute'):
            return client.post('/login', data={'email': email},
                               follow_redirects=False)

    def test_valid_email_redirects_to_dashboard(self, client):
        r = self._mock_login(client, 'oliver@company.com', DEMO_USER_ROW)
        assert r.status_code in (301, 302)
        assert 'dashboard' in r.headers.get('Location', '')

    def test_invalid_email_shows_error(self, client):
        r = self._mock_login(client, 'nobody@nowhere.com', None)
        # Should re-render login (200) or redirect to login
        assert r.status_code in (200, 302)

    def test_valid_login_sets_session_keys(self, client):
        self._mock_login(client, 'oliver@company.com', DEMO_USER_ROW)
        with client.session_transaction() as sess:
            assert sess.get('user_id')     == 'user-001'
            assert sess.get('employee_id') == 'emp-001'
            assert 'roles' in sess
            assert 'SYSTEM_ADMIN' in sess.get('roles', [])

    def test_login_stores_company_id_in_session(self, client):
        row = {**DEMO_USER_ROW, 'company_id': 'co-acme'}
        self._mock_login(client, 'oliver@company.com', row)
        with client.session_transaction() as sess:
            assert sess.get('company_id') == 'co-acme'

    def test_tech_admin_company_id_null_or_empty(self, client):
        """Tech Admin should have company_id = NULL — no company affiliation."""
        row = {**DEMO_USER_ROW, 'company_id': None}
        self._mock_login(client, 'oliver@company.com', row)
        with client.session_transaction() as sess:
            assert not sess.get('company_id'), \
                "Tech Admin's session company_id should be empty/None"

    def test_branding_loaded_into_session(self, client):
        brand = {'theme_color': '#ff0000', 'header_html': None,
                 'footer_html': None, 'logo_url': None, 'company_name': 'Acme'}
        row = {**DEMO_USER_ROW, 'company_id': 'co-001'}

        def query_side(sql, params=(), one=False):
            if 'companies' in sql:
                return brand if one else [brand]
            return row if one else [row]

        with patch('app.routes.auth.query', side_effect=query_side), \
             patch('app.routes.auth.execute'):
            client.post('/login', data={'email': 'x@x.com'})
        with client.session_transaction() as sess:
            assert sess.get('branding', {}).get('company_name') == 'Acme'

    def test_last_login_updated_on_success(self, client):
        with patch('app.routes.auth.query', return_value=DEMO_USER_ROW), \
             patch('app.routes.auth.execute') as mock_exec:
            client.post('/login', data={'email': 'oliver@company.com'})
        calls = [str(c) for c in mock_exec.call_args_list]
        assert any('last_login_at' in c for c in calls), \
            "last_login_at should be updated on successful login"


class TestLogout:
    def test_logout_clears_session(self, client):
        _set_session(client)
        client.get('/logout')
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_logout_redirects_to_login(self, client):
        _set_session(client)
        r = client.get('/logout')
        assert r.status_code in (301, 302)
        assert 'login' in r.headers.get('Location', '')

    def test_logout_without_session_redirects(self, client):
        r = client.get('/logout')
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────────────────
class TestAccessControl:
    """Protected routes must redirect unauthenticated users."""

    # Routes that must redirect when no session exists
    PROTECTED = ['/admin', '/admin/register-user', '/api/admin/users',
                 '/api/admin/org/business-units', '/api/admin/employees']

    def test_unauthenticated_gets_redirected(self, client):
        for path in self.PROTECTED:
            r = client.get(path)
            assert r.status_code in (301, 302), \
                f"Expected redirect for unauthenticated GET {path}, got {r.status_code}"

    def test_employee_cannot_access_admin(self, auth_client):
        r = auth_client.get('/admin')
        assert r.status_code == 302, "Employee should be redirected from /admin"

    def test_system_admin_can_access_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]):
            r = admin_client.get('/admin')
        assert r.status_code == 200

    def test_portal_admin_can_access_admin(self, client):
        _set_session(client, roles=['PORTAL_ADMIN', 'EMPLOYEE'])
        with client.session_transaction() as sess:
            sess['company_id'] = 'co-001'
        with patch('app.routes.admin.query', return_value=[]):
            r = client.get('/admin')
        assert r.status_code == 200, "Portal Admin should be able to access /admin"
