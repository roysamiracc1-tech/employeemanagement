"""
Integration tests for employee-related routes.
All DB interactions are mocked.
"""
import json
import pytest
from unittest.mock import patch

from tests.conftest import SAMPLE_EMPLOYEE, _set_session


class TestDirectoryRoute:
    def test_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/directory')
        assert response.status_code == 302

    def test_accessible_for_hr_admin(self, client):
        _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'])
        with patch('app.routes.employees.query', return_value=[]):
            response = client.get('/directory')
            assert response.status_code == 200

    def test_accessible_for_system_admin(self, admin_client):
        with patch('app.routes.employees.query', return_value=[]):
            response = admin_client.get('/directory')
            assert response.status_code == 200


class TestProfileRoute:
    def test_own_profile_loads(self, auth_client):
        with patch('app.routes.employees.fetch_employees', return_value=[SAMPLE_EMPLOYEE]), \
             patch('app.routes.employees.query', return_value=[]):
            response = auth_client.get('/profile')
            assert response.status_code == 200

    def test_other_profile_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/profile/other-emp-id')
        assert response.status_code == 302

    def test_other_profile_accessible_for_hr_admin(self, client):
        _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'], employee_id='admin-emp')
        with patch('app.routes.employees.fetch_employees', return_value=[SAMPLE_EMPLOYEE]), \
             patch('app.routes.employees.query', return_value=[]):
            response = client.get('/profile/emp-001')
            assert response.status_code == 200

    def test_profile_not_found_redirects(self, auth_client):
        with patch('app.routes.employees.fetch_employees', return_value=[]):
            response = auth_client.get('/profile')
            assert response.status_code == 302


class TestMyTeamRoute:
    def test_blocked_for_plain_employee(self, auth_client):
        response = auth_client.get('/my-team')
        assert response.status_code == 302

    def test_accessible_for_manager(self, manager_client):
        response = manager_client.get('/my-team')
        assert response.status_code == 200


class TestApiEmployees:
    def test_admin_gets_all_employees(self, admin_client):
        with patch('app.routes.employees.fetch_employees', return_value=[SAMPLE_EMPLOYEE]):
            response = admin_client.get('/api/employees')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1

    def test_manager_gets_direct_reports(self, manager_client):
        with patch('app.routes.employees.direct_report_ids', return_value=['emp-002']), \
             patch('app.routes.employees.fetch_employees', return_value=[SAMPLE_EMPLOYEE]):
            response = manager_client.get('/api/employees')
            assert response.status_code == 200

    def test_employee_gets_own_record(self, auth_client):
        with patch('app.routes.employees.fetch_employees', return_value=[SAMPLE_EMPLOYEE]):
            response = auth_client.get('/api/employees')
            assert response.status_code == 200


class TestProfileSelfEditApis:
    def test_save_skill_requires_login(self, client):
        response = client.post('/api/profile/skills',
                               data=json.dumps({'skill_id': 'sk-001'}),
                               content_type='application/json')
        assert response.status_code == 302

    def test_save_skill_missing_skill_id_returns_400(self, auth_client):
        response = auth_client.post('/api/profile/skills',
                                    data=json.dumps({}),
                                    content_type='application/json')
        assert response.status_code == 400

    def test_save_skill_succeeds(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.post('/api/profile/skills',
                                        data=json.dumps({'skill_id': 'sk-001', 'level_id': 'lv-001'}),
                                        content_type='application/json')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True

    def test_delete_skill_succeeds(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.delete('/api/profile/skills/sk-001')
            assert response.status_code == 200

    def test_save_gender_invalid_value_returns_400(self, auth_client):
        response = auth_client.post('/api/profile/gender',
                                    data=json.dumps({'gender': 'UNKNOWN'}),
                                    content_type='application/json')
        assert response.status_code == 400

    def test_save_gender_valid_value_succeeds(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.post('/api/profile/gender',
                                        data=json.dumps({'gender': 'female'}),
                                        content_type='application/json')
            assert response.status_code == 200

    def test_add_cert_missing_cert_id_returns_400(self, auth_client):
        response = auth_client.post('/api/profile/certifications',
                                    data=json.dumps({}),
                                    content_type='application/json')
        assert response.status_code == 400

    def test_add_cert_succeeds(self, auth_client):
        with patch('app.routes.employees.insert_returning', return_value={'id': 'ec-001'}):
            response = auth_client.post('/api/profile/certifications',
                                        data=json.dumps({'cert_id': 'cert-001'}),
                                        content_type='application/json')
            assert response.status_code == 200

    def test_delete_cert_succeeds(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.delete('/api/profile/certifications/ec-001')
            assert response.status_code == 200


class TestUserThemeApi:
    def test_invalid_theme_returns_400(self, auth_client):
        response = auth_client.post('/api/user/theme',
                                    data=json.dumps({'theme': 'rainbow'}),
                                    content_type='application/json')
        assert response.status_code == 400

    def test_valid_dark_theme_saved(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.post('/api/user/theme',
                                        data=json.dumps({'theme': 'dark'}),
                                        content_type='application/json')
            assert response.status_code == 200
            assert json.loads(response.data)['theme'] == 'dark'

    def test_valid_light_theme_saved(self, auth_client):
        with patch('app.routes.employees.execute'):
            response = auth_client.post('/api/user/theme',
                                        data=json.dumps({'theme': 'light'}),
                                        content_type='application/json')
            assert response.status_code == 200
