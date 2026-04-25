"""
Integration tests for vacation routes.
All DB interactions are mocked.
"""
import json
import datetime
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import SAMPLE_VACATION_TYPE


class TestVacationPage:
    def test_vacation_page_loads_for_employee(self, auth_client):
        vt = {**SAMPLE_VACATION_TYPE, 'used_days': 3, 'remaining': 17, 'rules': [], 'rule_labels': []}
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]), \
             patch('app.routes.vacation.used_days', return_value=3), \
             patch('app.routes.vacation.query', return_value=[]):
            response = auth_client.get('/vacation')
            assert response.status_code == 200

    def test_vacation_page_shows_no_manager_warning(self, auth_client):
        with patch('app.routes.vacation.employee_solid_manager', return_value=None), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[]), \
             patch('app.routes.vacation.query', return_value=[]):
            response = auth_client.get('/vacation')
            assert response.status_code == 200
            assert b'No manager' in response.data or b'no manager' in response.data.lower()


class TestVacationSubmit:
    def _post(self, client, payload):
        return client.post(
            '/api/vacation/request',
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_submit_requires_login(self, client):
        response = self._post(client, {})
        assert response.status_code == 302

    def test_submit_fails_without_manager(self, auth_client):
        with patch('app.routes.vacation.employee_solid_manager', return_value=None):
            response = self._post(auth_client, {
                'vacation_type_id': 'vt-001',
                'start_date': '2026-07-01',
                'end_date': '2026-07-05',
            })
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'No manager' in data['error']

    def test_submit_fails_with_missing_fields(self, auth_client):
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'):
            response = self._post(auth_client, {'vacation_type_id': 'vt-001'})
            assert response.status_code == 400

    def test_submit_fails_for_ineligible_vacation_type(self, auth_client):
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[]):
            response = self._post(auth_client, {
                'vacation_type_id': 'vt-restricted',
                'start_date': '2026-07-01',
                'end_date': '2026-07-05',
            })
            assert response.status_code == 403

    def test_submit_fails_when_end_before_start(self, auth_client):
        vt = {**SAMPLE_VACATION_TYPE}
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]):
            response = self._post(auth_client, {
                'vacation_type_id': 'vt-001',
                'start_date': '2026-07-10',
                'end_date': '2026-07-05',
            })
            assert response.status_code == 400
            assert 'End date' in json.loads(response.data)['error']

    def test_submit_fails_when_annual_limit_exceeded(self, auth_client):
        vt = {**SAMPLE_VACATION_TYPE, 'max_days_per_year': 5}
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]), \
             patch('app.routes.vacation.used_days', return_value=4), \
             patch('app.routes.vacation.query', return_value={'max_days_per_year': 5}):
            response = self._post(auth_client, {
                'vacation_type_id': 'vt-001',
                'start_date': '2026-07-01',
                'end_date': '2026-07-05',  # 3 working days → 4+3=7 > 5
            })
            assert response.status_code == 400
            assert 'limit' in json.loads(response.data)['error'].lower()

    def test_submit_succeeds_with_valid_data(self, auth_client):
        vt = {**SAMPLE_VACATION_TYPE}
        with patch('app.routes.vacation.employee_solid_manager', return_value='mgr-001'), \
             patch('app.routes.vacation.vacation_types_for_employee', return_value=[vt]), \
             patch('app.routes.vacation.query', return_value={'max_days_per_year': None}), \
             patch('app.routes.vacation.insert_returning', return_value={'id': 'req-001'}):
            response = self._post(auth_client, {
                'vacation_type_id': 'vt-001',
                'start_date': '2026-07-01',
                'end_date': '2026-07-03',
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['ok'] is True
            assert data['working_days'] == 3


class TestVacationCancel:
    def test_cancel_requires_login(self, client):
        response = client.delete('/api/vacation/request/req-001')
        assert response.status_code == 302

    def test_cancel_not_found_returns_404(self, auth_client):
        with patch('app.routes.vacation.query', return_value=None):
            response = auth_client.delete('/api/vacation/request/req-999')
            assert response.status_code == 404

    def test_cancel_non_pending_returns_400(self, auth_client):
        with patch('app.routes.vacation.query', return_value={'status': 'APPROVED'}):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 400
            assert 'PENDING' in json.loads(response.data)['error']

    def test_cancel_pending_succeeds(self, auth_client):
        with patch('app.routes.vacation.query', return_value={'status': 'PENDING'}), \
             patch('app.routes.vacation.execute'):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True


class TestVacationReview:
    def _review(self, client, req_id, action, note=None):
        return client.post(
            f'/api/vacation/review/{req_id}',
            data=json.dumps({'action': action, 'note': note}),
            content_type='application/json',
        )

    def test_review_blocked_for_plain_employee(self, auth_client):
        response = self._review(auth_client, 'req-001', 'approve')
        assert response.status_code == 302

    def test_review_invalid_action_returns_400(self, manager_client):
        response = self._review(manager_client, 'req-001', 'maybe')
        assert response.status_code == 400

    def test_review_not_found_returns_404(self, manager_client):
        with patch('app.routes.vacation.query', return_value=None):
            response = self._review(manager_client, 'req-999', 'approve')
            assert response.status_code == 404

    def test_review_already_actioned_returns_400(self, manager_client):
        with patch('app.routes.vacation.query', return_value={'status': 'APPROVED'}):
            response = self._review(manager_client, 'req-001', 'approve')
            assert response.status_code == 400

    def test_approve_sets_approved_status(self, manager_client):
        with patch('app.routes.vacation.query', return_value={'status': 'PENDING'}), \
             patch('app.routes.vacation.execute') as mock_exec:
            response = self._review(manager_client, 'req-001', 'approve', note='Approved!')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'APPROVED'

    def test_reject_sets_rejected_status(self, manager_client):
        with patch('app.routes.vacation.query', return_value={'status': 'PENDING'}), \
             patch('app.routes.vacation.execute'):
            response = self._review(manager_client, 'req-001', 'reject', note='Too short notice')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'REJECTED'
