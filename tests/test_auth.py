"""
Unit tests for app/auth.py — login_required and require_roles decorators.
"""
import pytest
from unittest.mock import patch
from flask import session


class TestLoginRequired:
    def test_redirects_to_login_when_not_authenticated(self, client):
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_allows_access_when_authenticated(self, auth_client):
        with patch('app.routes.dashboard.compute_dashboard_stats', return_value={'own': {}}), \
             patch('app.routes.dashboard.get_refresh_interval', return_value=30000):
            response = auth_client.get('/dashboard')
            assert response.status_code == 200

    def test_protects_profile_route(self, client):
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_protects_vacation_route(self, client):
        response = client.get('/vacation')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_protects_api_employees(self, client):
        response = client.get('/api/employees')
        assert response.status_code == 302


class TestRequireRoles:
    def test_admin_route_blocked_for_employee(self, auth_client):
        response = auth_client.get('/admin')
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

    def test_admin_route_accessible_for_system_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]):
            response = admin_client.get('/admin')
            assert response.status_code == 200

    def test_directory_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/directory')
        assert response.status_code == 302

    def test_directory_accessible_for_hr_admin(self, client):
        from tests.conftest import _set_session
        _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'])
        with patch('app.routes.employees.query', return_value=[]):
            response = client.get('/directory')
            assert response.status_code == 200

    def test_org_tree_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/org-tree')
        assert response.status_code == 302

    def test_org_tree_accessible_for_manager(self, manager_client):
        with patch('app.routes.org.query', return_value=[]):
            response = manager_client.get('/org-tree')
            assert response.status_code == 200

    def test_vacation_team_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/vacation/team')
        assert response.status_code == 302

    def test_vacation_team_accessible_for_manager(self, manager_client):
        response = manager_client.get('/vacation/team')
        assert response.status_code == 200


class TestLoginRoute:
    def test_login_page_loads(self, client):
        with patch('app.routes.auth.query', return_value=[]):
            response = client.get('/login')
            assert response.status_code == 200

    def test_login_redirects_to_dashboard_if_already_logged_in(self, auth_client):
        response = auth_client.get('/login')
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

    def test_login_post_unknown_email_shows_error(self, client):
        with patch('app.routes.auth.query', side_effect=[None, []]):
            response = client.post('/login', data={'email': 'nobody@example.com'},
                                   follow_redirects=True)
            assert response.status_code == 200
            assert b'No active account' in response.data

    def test_logout_clears_session_and_redirects(self, auth_client):
        response = auth_client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_logout_clears_session_data(self, auth_client):
        auth_client.get('/logout')
        with auth_client.session_transaction() as sess:
            assert 'user_id' not in sess
