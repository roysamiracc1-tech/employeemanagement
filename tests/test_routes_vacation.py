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

    def test_cancel_already_started_approved_returns_400(self, auth_client):
        import datetime
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        with patch('app.routes.vacation.query',
                   return_value={'status': 'APPROVED', 'start_date': yesterday}):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 400
            assert 'started' in json.loads(response.data)['error'].lower()

    def test_cancel_rejected_returns_400(self, auth_client):
        with patch('app.routes.vacation.query',
                   return_value={'status': 'REJECTED', 'start_date': '2026-12-01'}):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 400

    def test_withdraw_future_approved_succeeds(self, auth_client):
        import datetime
        future = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        call_count = {'n': 0}

        def side(sql, *args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                return {'status': 'APPROVED', 'start_date': future}
            if call_count['n'] == 2:
                return {
                    'manager_id': 'mgr-001', 'start_date': future,
                    'end_date': future, 'working_days': 1,
                    'vacation_type': 'Annual Leave', 'company_id': 'co-001',
                    'employee_name': 'Sven Becker',
                }
            if call_count['n'] == 3:
                return {'id': 'user-mgr-001'}
            return None

        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification'):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True

    def _cancel_query_side(self):
        """Return mock rows for the three queries in api_vacation_cancel."""
        call_count = {'n': 0}

        def side(sql, *args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                # First query: ownership + status check
                return {'status': 'PENDING', 'start_date': '2026-06-02'}
            if call_count['n'] == 2:
                # Second query: full request for notification
                return {
                    'manager_id':    'mgr-001',
                    'start_date':    '2026-06-02',
                    'end_date':      '2026-06-03',
                    'working_days':  2,
                    'vacation_type': 'Annual Leave',
                    'company_id':    'co-001',
                    'employee_name': 'Sven Becker',
                }
            if call_count['n'] == 3:
                # Third query: manager's user_id
                return {'id': 'user-mgr-001'}
            return None

        return side

    def test_cancel_pending_succeeds(self, auth_client):
        with patch('app.routes.vacation.query',
                   return_value={'status': 'PENDING', 'start_date': '2026-06-02'}), \
             patch('app.routes.vacation.execute'):
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 200
            assert json.loads(response.data)['ok'] is True

    def test_cancel_triggers_manager_notification(self, auth_client):
        side = self._cancel_query_side()
        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 200
            # Manager must receive an in-app notification
            mock_notif.assert_called_once()
            args = mock_notif.call_args[0]
            assert args[0] == 'user-mgr-001'           # correct manager user_id
            assert args[1] == 'VACATION_CANCELLED'      # correct event
            assert 'cancelled' in args[2].lower()       # message says cancelled
            assert 'Sven Becker' in args[2]             # names the employee

    def test_cancel_manager_notification_link_is_team_page(self, auth_client):
        side = self._cancel_query_side()
        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            auth_client.delete('/api/vacation/request/req-001')
            kwargs = mock_notif.call_args[1]
            assert kwargs.get('link') == '/vacation/team'

    def test_cancel_without_manager_user_still_succeeds(self, auth_client):
        """Cancellation must succeed even when manager has no user account."""
        call_count = {'n': 0}

        def side(sql, *args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                return {'status': 'PENDING'}
            if call_count['n'] == 2:
                return {
                    'manager_id': 'mgr-no-user', 'start_date': '2026-06-02',
                    'end_date': '2026-06-03', 'working_days': 2,
                    'vacation_type': 'Annual Leave', 'company_id': 'co-001',
                    'employee_name': 'Test User',
                }
            return None  # no user row for this manager

        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            response = auth_client.delete('/api/vacation/request/req-001')
            assert response.status_code == 200
            mock_notif.assert_not_called()  # no user → no notification, no crash


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

    def _query_side_effect_for_review(self, new_status):
        """Return the correct mock row depending on which query is called."""
        call_count = {'n': 0}

        def side(sql, *args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                # First query: check request status + ownership
                return {'status': 'PENDING'}
            if call_count['n'] == 2:
                # Second query: fetch full request for notification
                return {
                    'employee_id': 'emp-002',
                    'start_date':  '2026-06-02',
                    'end_date':    '2026-06-03',
                    'working_days': 2,
                    'vacation_type': 'Annual Leave',
                    'company_id': 'co-001',
                }
            if call_count['n'] == 3:
                # Third query: look up employee user_id for in-app notification
                return {'id': 'user-emp-002'}
            return None

        return side

    def test_approve_sets_approved_status(self, manager_client):
        side = self._query_side_effect_for_review('APPROVED')
        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            response = self._review(manager_client, 'req-001', 'approve', note='Approved!')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'APPROVED'
            # Employee must receive an in-app notification
            mock_notif.assert_called_once()
            args = mock_notif.call_args[0]
            assert args[0] == 'user-emp-002'          # correct user_id
            assert args[1] == 'VACATION_APPROVED'      # correct event
            assert 'approved' in args[2].lower()       # message says approved

    def test_reject_sets_rejected_status(self, manager_client):
        side = self._query_side_effect_for_review('REJECTED')
        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            response = self._review(manager_client, 'req-001', 'reject', note='Too short notice')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'REJECTED'
            mock_notif.assert_called_once()
            args = mock_notif.call_args[0]
            assert args[0] == 'user-emp-002'
            assert args[1] == 'VACATION_REJECTED'
            assert 'rejected' in args[2].lower()

    def test_approve_without_employee_user_still_succeeds(self, manager_client):
        """Approval must succeed even if the employee has no user account."""
        call_count = {'n': 0}

        def side(sql, *args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                return {'status': 'PENDING'}
            if call_count['n'] == 2:
                return {
                    'employee_id': 'emp-no-user',
                    'start_date': '2026-06-02', 'end_date': '2026-06-03',
                    'working_days': 2, 'vacation_type': 'Annual Leave',
                    'company_id': 'co-001',
                }
            return None  # no user row found

        with patch('app.routes.vacation.query', side_effect=side), \
             patch('app.routes.vacation.execute'), \
             patch('app.services.notification_service.dispatch'), \
             patch('app.services.notification_service.create_user_notification') as mock_notif:
            response = self._review(manager_client, 'req-001', 'approve')
            assert response.status_code == 200
            mock_notif.assert_not_called()  # no user → no notification, but no crash


class TestMyNotificationsAPI:
    """Tests for GET /api/my-notifications and POST /api/my-notifications/mark-read."""

    def test_my_notifications_requires_login(self, app):
        client = app.test_client()
        response = client.get('/api/my-notifications')
        assert response.status_code in (302, 401)

    def test_my_notifications_returns_empty_list(self, auth_client):
        with patch('app.services.notification_service.get_unread_notifications',
                   return_value=[]):
            response = auth_client.get('/api/my-notifications')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['count'] == 0
            assert data['notifications'] == []

    def test_my_notifications_returns_unread_items(self, auth_client):
        fake_notifs = [
            {
                'id': 'notif-001',
                'event_type': 'VACATION_APPROVED',
                'message': 'Your Annual Leave (2026-06-02 → 2026-06-03) has been approved.',
                'link': '/vacation',
                'created_at': '2026-06-01 10:00:00',
            }
        ]
        with patch('app.services.notification_service.get_unread_notifications',
                   return_value=fake_notifs):
            response = auth_client.get('/api/my-notifications')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['count'] == 1
            assert data['notifications'][0]['event_type'] == 'VACATION_APPROVED'
            assert 'approved' in data['notifications'][0]['message'].lower()

    def test_mark_read_requires_login(self, app):
        client = app.test_client()
        response = client.post('/api/my-notifications/mark-read')
        assert response.status_code in (302, 401)

    def test_mark_read_calls_service(self, auth_client):
        with patch('app.services.notification_service.mark_all_read') as mock_mark:
            response = auth_client.post('/api/my-notifications/mark-read')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['ok'] is True
            mock_mark.assert_called_once()
