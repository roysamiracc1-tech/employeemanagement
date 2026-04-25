"""
Integration tests for admin routes.
All DB interactions are mocked.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session


class TestAdminPanel:
    def test_blocked_for_employee(self, auth_client):
        response = auth_client.get('/admin')
        assert response.status_code == 302

    def test_accessible_for_system_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]):
            response = admin_client.get('/admin')
            assert response.status_code == 200


class TestAdminRegisterUser:
    def test_blocked_for_non_admin(self, auth_client):
        response = auth_client.get('/admin/register-user')
        assert response.status_code == 302

    def test_get_form_loads_for_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]), \
             patch('app.routes.admin.next_employee_number', return_value='EMP-099'):
            response = admin_client.get('/admin/register-user')
            assert response.status_code == 200

    def test_post_missing_name_redirects_with_error(self, admin_client):
        # query returns None for uniqueness checks (not found = ok), [] for list queries
        def mock_query(sql, params=(), one=False):
            return None if one else []

        with patch('app.routes.admin.query', side_effect=mock_query), \
             patch('app.routes.admin.next_employee_number', return_value='EMP-099'):
            response = admin_client.post('/admin/register-user', data={
                'first_name': '', 'last_name': '', 'emp_email': 'x@x.com',
                'employee_number': 'EMP-099', 'username': 'xuser',
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_post_duplicate_email_shows_error(self, admin_client):
        def mock_query(sql, params=(), one=False):
            if 'LOWER(email)' in sql:
                return {'email': 'existing@example.com'} if one else []
            return None if one else []

        with patch('app.routes.admin.query', side_effect=mock_query), \
             patch('app.routes.admin.next_employee_number', return_value='EMP-099'):
            response = admin_client.post('/admin/register-user', data={
                'first_name': 'Test', 'last_name': 'User',
                'emp_email': 'existing@example.com',
                'employee_number': 'EMP-099', 'username': 'testuser',
            }, follow_redirects=True)
            assert response.status_code == 200


class TestApiAdminUsers:
    def test_blocked_for_non_admin(self, auth_client):
        response = auth_client.get('/api/admin/users')
        assert response.status_code == 302

    def test_returns_user_list_for_admin(self, admin_client):
        mock_user = {
            'id': 'user-001', 'username': 'jsmith', 'email': 'j@x.com',
            'is_active': True, 'last_login_at': None,
            'employee_number': 'EMP-001', 'first_name': 'Jane', 'last_name': 'Smith',
            'job_title': 'Engineer', 'employee_id': 'emp-001',
            'employment_status': 'ACTIVE', 'location': 'London',
            'roles': ['EMPLOYEE'],
        }
        with patch('app.routes.admin.query', return_value=[mock_user]):
            response = admin_client.get('/api/admin/users')
            assert response.status_code == 200


class TestApiUpdateRoles:
    def test_blocked_for_non_admin(self, auth_client):
        response = auth_client.post('/api/admin/update-roles',
                                    data=json.dumps({'user_id': 'u1', 'roles': []}),
                                    content_type='application/json')
        assert response.status_code == 302

    def test_missing_user_id_returns_400(self, admin_client):
        response = admin_client.post('/api/admin/update-roles',
                                     data=json.dumps({'roles': ['EMPLOYEE']}),
                                     content_type='application/json')
        assert response.status_code == 400

    def test_valid_update_succeeds(self, admin_client):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_db.cursor.return_value.__exit__ = MagicMock(return_value=False)
        with patch('app.routes.admin.get_db', return_value=mock_db):
            response = admin_client.post('/api/admin/update-roles',
                                         data=json.dumps({'user_id': 'u1', 'roles': ['HR_ADMIN']}),
                                         content_type='application/json')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True


class TestApiToggleUser:
    def test_blocked_for_non_admin(self, auth_client):
        response = auth_client.post('/api/admin/toggle-user',
                                    data=json.dumps({'user_id': 'u1'}),
                                    content_type='application/json')
        assert response.status_code == 302

    def test_toggle_deactivates_user(self, admin_client):
        with patch('app.routes.admin.execute'), \
             patch('app.routes.admin.query', return_value={'is_active': False}):
            response = admin_client.post('/api/admin/toggle-user',
                                         data=json.dumps({'user_id': 'u1'}),
                                         content_type='application/json')
            assert response.status_code == 200
            assert json.loads(response.data)['is_active'] is False


class TestApiValidateSkill:
    def test_blocked_for_plain_employee(self, auth_client):
        response = auth_client.post('/api/admin/validate-skill',
                                    data=json.dumps({'skill_id': 'es-001', 'level': 'Expert'}),
                                    content_type='application/json')
        assert response.status_code == 302

    def test_validation_succeeds_for_admin(self, admin_client):
        with patch('app.routes.admin.execute'):
            response = admin_client.post('/api/admin/validate-skill',
                                         data=json.dumps({'skill_id': 'es-001', 'level': 'Expert', 'status': 'VALIDATED'}),
                                         content_type='application/json')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True


class TestAdminCompanies:
    def test_blocked_for_non_admin(self, auth_client):
        response = auth_client.get('/admin/companies')
        assert response.status_code == 302

    def test_list_loads_for_admin(self, admin_client):
        with patch('app.routes.company.query', return_value=[]):
            response = admin_client.get('/admin/companies')
            assert response.status_code == 200

    def test_new_company_form_loads(self, admin_client):
        response = admin_client.get('/admin/companies/new')
        assert response.status_code == 200

    def test_new_company_post_missing_name_redirects(self, admin_client):
        response = admin_client.post('/admin/companies/new', data={'name': ''},
                                     follow_redirects=True)
        assert response.status_code == 200
