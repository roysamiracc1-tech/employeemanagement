"""
Integration tests for the 5 roadmap features:
  1. Email notifications (config API, mute API)
  2. Full-text search (employee, vacation, org)
  3. Vacation calendar (mine, team, all scopes)
  4. Bulk employee import (upload, approve, process)
  5. Mobile responsive (CSS classes present, meta viewport, overlay element)
All DB calls are mocked.
"""
import json
import io
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session

# ── Shared IDs ───────────────────────────────────────────────────────────────

CO_ID  = '709a1ece-0000-0000-0000-000000000001'
EMP_ID = 'emp00001-0000-0000-0000-000000000001'
MGR_ID = 'mgr00001-0000-0000-0000-000000000001'
USR_ID = 'usr00001-0000-0000-0000-000000000001'
IMP_ID = 'imp00001-0000-0000-0000-000000000001'


def _admin(client):
    _set_session(client, roles=['SYSTEM_ADMIN', 'EMPLOYEE'])
    with client.session_transaction() as s:
        s['company_id']       = None
        s['admin_company_id'] = CO_ID
    return client


def _portal(client):
    _set_session(client, roles=['PORTAL_ADMIN', 'EMPLOYEE'])
    with client.session_transaction() as s:
        s['company_id'] = CO_ID
    return client


def _hr(client):
    _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'])
    with client.session_transaction() as s:
        s['company_id'] = CO_ID
    return client


# ─────────────────────────────────────────────────────────────────────────────
# 1. NOTIFICATION SETTINGS API
# ─────────────────────────────────────────────────────────────────────────────

class TestNotificationSettingsApi:

    def test_get_settings_requires_admin(self, auth_client):
        r = auth_client.get(f'/api/notifications/settings?company_id={CO_ID}')
        assert r.status_code == 302

    def test_get_settings_returns_matrix(self, client):
        _admin(client)
        mock_rows = [
            {'event_type': 'VACATION_REQUESTED', 'recipient_role': 'SOLID_LINE_MANAGER',
             'is_enabled': True, 'allow_mute': False},
        ]
        with patch('app.routes.notifications.query', return_value=mock_rows):
            r = client.get(f'/api/notifications/settings?company_id={CO_ID}')
        assert r.status_code == 200
        data = r.get_json()
        assert 'event_types' in data
        assert 'matrix'      in data
        assert 'VACATION_REQUESTED' in data['event_types']

    def test_update_settings_invalid_event(self, client):
        _admin(client)
        with patch('app.routes.notifications.execute'):
            r = client.post('/api/notifications/settings',
                            data=json.dumps({'event_type': 'BOGUS_EVENT',
                                             'recipient_role': 'EMPLOYEE',
                                             'company_id': CO_ID}),
                            content_type='application/json')
        assert r.status_code == 400

    def test_update_settings_with_inherit(self, client):
        _admin(client)
        with patch('app.routes.notifications.execute') as mock_exec:
            r = client.post('/api/notifications/settings',
                            data=json.dumps({
                                'event_type':     'VACATION_APPROVED',
                                'recipient_role': 'SOLID_LINE_MANAGER',
                                'is_enabled':     True,
                                'allow_mute':     True,
                                'inherit':        True,
                                'company_id':     CO_ID,
                            }),
                            content_type='application/json')
        assert r.status_code == 200
        data = r.get_json()
        assert data['ok'] is True
        # inherit=True → should update SOLID_LINE_MANAGER + DOTTED_LINE_MANAGER + EMPLOYEE
        assert len(data['updated_roles']) > 1

    def test_mute_notification(self, auth_client):
        with patch('app.routes.notifications.query', return_value={'exists': True}), \
             patch('app.routes.notifications.execute'):
            r = auth_client.post('/api/notifications/mute',
                                 data=json.dumps({'event_type': 'VACATION_APPROVED',
                                                  'mute': True}),
                                 content_type='application/json')
        assert r.status_code in (200, 403)  # 403 if allow_mute is False in mock

    def test_my_mutes_returns_list(self, auth_client):
        with patch('app.routes.notifications.query', return_value=[
            {'event_type': 'VACATION_APPROVED'}
        ]):
            r = auth_client.get('/api/notifications/my-mutes')
        assert r.status_code == 200
        assert 'VACATION_APPROVED' in r.get_json()

    def test_unauthenticated_blocked(self, client):
        r = client.get('/api/notifications/my-mutes')
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────────────────
# 2. FULL-TEXT SEARCH
# ─────────────────────────────────────────────────────────────────────────────

class TestSearchApi:

    EMPLOYEE_ROW = {
        'id': EMP_ID, 'first_name': 'Oliver', 'last_name': 'Hartmann',
        'job_title': 'Engineer', 'email': 'o@company.com',
        'employment_status': 'ACTIVE', 'location': 'London', 'business_unit': 'Eng',
    }

    def test_search_page_accessible(self, auth_client):
        r = auth_client.get('/search')
        assert r.status_code == 200
        assert b'srch-input' in r.data

    def test_search_api_returns_structure(self, auth_client):
        with patch('app.routes.search.unified_search', return_value={
            'employees': [self.EMPLOYEE_ROW], 'vacations': [], 'org': None
        }):
            r = auth_client.get('/api/search?q=Oliver')
        assert r.status_code == 200
        data = r.get_json()
        assert 'employees' in data
        assert 'vacations' in data
        assert 'org'       in data

    def test_short_query_returns_empty(self, auth_client):
        r = auth_client.get('/api/search?q=a')
        assert r.status_code == 200
        data = r.get_json()
        assert data['employees'] == []

    def test_org_intent_reporting_to_me(self, auth_client):
        with patch('app.routes.search.unified_search', return_value={
            'employees': [],
            'vacations': [],
            'org': {'action': 'focus_tree', 'root_id': EMP_ID,
                    'label': 'People reporting to you'},
        }):
            r = auth_client.get('/api/search?q=people+reporting+to+me')
        data = r.get_json()
        assert data['org'] is not None
        assert data['org']['action'] == 'focus_tree'

    def test_search_requires_login(self, client):
        r = client.get('/api/search?q=test')
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────────────────
# 3. VACATION CALENDAR
# ─────────────────────────────────────────────────────────────────────────────

class TestVacationCalendar:

    def test_calendar_page_accessible(self, auth_client):
        r = auth_client.get('/vacation/calendar')
        assert r.status_code == 200
        assert b'cal-grid' in r.data

    def test_calendar_api_mine(self, auth_client):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda s, k: {
            'id': 'vr1', 'start_date': '2026-05-05', 'end_date': '2026-05-07',
            'status': 'APPROVED', 'working_days': 3, 'type_name': 'Annual Leave',
            'color': '#3b82f6', 'employee_id': EMP_ID, 'employee_name': 'Oliver Hartmann',
        }[k]
        mock_row.keys = lambda: ['id','start_date','end_date','status','working_days',
                                  'type_name','color','employee_id','employee_name']
        with patch('app.routes.calendar.query', return_value=[mock_row]):
            r = auth_client.get('/api/vacation/calendar?year=2026&month=5&scope=mine')
        assert r.status_code == 200
        data = r.get_json()
        assert 'events_by_date' in data
        assert data['year']  == 2026
        assert data['month'] == 5

    def test_calendar_api_team_scope(self, manager_client):
        with patch('app.routes.calendar.query', return_value=[]):
            r = manager_client.get('/api/vacation/calendar?scope=team&year=2026&month=5')
        assert r.status_code == 200

    def test_calendar_api_all_scope_with_company(self, client):
        _portal(client)
        with patch('app.routes.calendar.query', return_value=[]):
            r = client.get('/api/vacation/calendar?scope=all&year=2026&month=5')
        assert r.status_code == 200

    def test_calendar_nav_link_in_base(self, auth_client):
        """Leave Calendar link must appear in the sidebar for all users."""
        with patch('app.routes.dashboard.compute_dashboard_stats', return_value={'own': {}}), \
             patch('app.routes.dashboard.get_refresh_interval', return_value=30000), \
             patch('app.routes.dashboard.query', return_value=[]):
            r = auth_client.get('/dashboard')
        assert r.status_code == 200
        assert b'Leave Calendar' in r.data or b'vacation_calendar' in r.data

    def test_calendar_requires_login(self, client):
        r = client.get('/vacation/calendar')
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────────────────
# 4. BULK EMPLOYEE IMPORT
# ─────────────────────────────────────────────────────────────────────────────

VALID_CSV = b"first_name,last_name,email,job_title\nAnna,Smith,anna@test.com,Engineer\n"
INVALID_CSV = b"first_name,last_name\nAnna,Smith\n"  # missing email column


class TestBulkImport:

    def test_import_list_accessible_to_admin(self, client):
        _portal(client)
        with patch('app.routes.imports.query', return_value=[]):
            r = client.get('/admin/imports')
        assert r.status_code == 200

    def test_import_list_blocked_for_employee(self, auth_client):
        r = auth_client.get('/admin/imports')
        assert r.status_code == 302

    def test_upload_page_accessible(self, client):
        _portal(client)
        r = client.get('/admin/imports/upload')
        assert r.status_code == 200
        assert b'drop-zone' in r.data

    def test_upload_valid_csv(self, client):
        _portal(client)
        def mock_query(sql, params=(), one=False):
            if 'LOWER(email)' in sql or 'employees WHERE' in sql.lower():
                return None  # email not taken
            return [] if not one else None

        with patch('app.routes.imports.import_service.parse_and_validate',
                   return_value=([{'row_number':1,'raw_data':{},'validation_errors':None,'status':'VALID'}],
                                  {'row_count':1,'valid_count':1,'error_count':0})), \
             patch('app.routes.imports.import_service.create_import_record',
                   return_value=IMP_ID), \
             patch('app.routes.imports.execute'):
            r = client.post('/api/admin/imports/upload',
                            data={'csv_file': (io.BytesIO(VALID_CSV), 'employees.csv')},
                            content_type='multipart/form-data')
        assert r.status_code == 200
        data = r.get_json()
        assert 'import_id' in data

    def test_upload_missing_file_400(self, client):
        _portal(client)
        r = client.post('/api/admin/imports/upload')
        assert r.status_code == 400

    def test_upload_non_csv_rejected(self, client):
        _portal(client)
        r = client.post('/api/admin/imports/upload',
                        data={'csv_file': (io.BytesIO(b'data'), 'file.xlsx')},
                        content_type='multipart/form-data')
        assert r.status_code == 400

    def test_approve_import_requires_portal_admin(self, client):
        _hr(client)
        r = client.post(f'/api/admin/imports/{IMP_ID}/approve')
        assert r.status_code == 302

    def test_approve_import_succeeds(self, client):
        _portal(client)
        with patch('app.routes.imports.query',
                   return_value={'status': 'PENDING_REVIEW', 'company_id': CO_ID}), \
             patch('app.routes.imports.execute'):
            r = client.post(f'/api/admin/imports/{IMP_ID}/approve')
        assert r.status_code == 200
        assert r.get_json()['ok'] is True

    def test_approve_wrong_status_400(self, client):
        _portal(client)
        with patch('app.routes.imports.query',
                   return_value={'status': 'COMPLETED', 'company_id': CO_ID}):
            r = client.post(f'/api/admin/imports/{IMP_ID}/approve')
        assert r.status_code == 400

    def test_process_requires_approved_status(self, client):
        _portal(client)
        with patch('app.routes.imports.query',
                   return_value={'status': 'PENDING_REVIEW', 'company_id': CO_ID}):
            r = client.post(f'/api/admin/imports/{IMP_ID}/process')
        assert r.status_code == 400

    def test_process_approved_import(self, client):
        _portal(client)
        with patch('app.routes.imports.query',
                   return_value={'status': 'APPROVED', 'company_id': CO_ID}), \
             patch('app.routes.imports.execute'), \
             patch('app.routes.imports.import_service.apply_import',
                   return_value={'imported': 1, 'failed': 0}):
            r = client.post(f'/api/admin/imports/{IMP_ID}/process')
        assert r.status_code == 200
        assert r.get_json()['imported'] == 1


# ─────────────────────────────────────────────────────────────────────────────
# 5. MOBILE RESPONSIVE
# ─────────────────────────────────────────────────────────────────────────────

class TestMobileResponsive:

    def _dash(self, auth_client):
        with patch('app.routes.dashboard.compute_dashboard_stats', return_value={'own': {}}), \
             patch('app.routes.dashboard.get_refresh_interval', return_value=30000), \
             patch('app.routes.dashboard.query', return_value=[]):
            return auth_client.get('/dashboard')

    def test_viewport_meta_present(self, auth_client):
        r = self._dash(auth_client)
        assert b'viewport' in r.data
        assert b'width=device-width' in r.data

    def test_mobile_overlay_element_present(self, auth_client):
        r = self._dash(auth_client)
        assert b'mob-overlay' in r.data

    def test_mobile_css_classes_in_stylesheet(self):
        with open('static/css/style.css') as f:
            css = f.read()
        for cls in ('.cal-cell', '.cal-grid', '.import-drop-zone',
                    '.srch-emp-row', '.topbar-search',
                    'max-width: 767px', '#mob-overlay'):
            assert cls in css, f"Missing CSS: {cls}"

    def test_responsive_media_query_present(self):
        with open('static/css/style.css') as f:
            css = f.read()
        assert '@media (max-width: 767px)' in css

    def test_search_bar_in_topbar(self, auth_client):
        r = self._dash(auth_client)
        assert b'topbar-search' in r.data


# ─────────────────────────────────────────────────────────────────────────────
# 6. SERVICE LAYER UNIT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanyScopeService:

    def test_current_company_id_system_admin(self, client):
        """SYSTEM_ADMIN returns admin_company_id."""
        from app.services.company_scope import current_company_id
        _admin(client)
        with client.application.test_request_context():
            from flask import session
            session['roles'] = ['SYSTEM_ADMIN']
            session['admin_company_id'] = CO_ID
            assert current_company_id() == CO_ID

    def test_current_company_id_portal_admin(self, client):
        from app.services.company_scope import current_company_id
        _portal(client)
        with client.application.test_request_context():
            from flask import session
            session['roles'] = ['PORTAL_ADMIN']
            session['company_id'] = CO_ID
            assert current_company_id() == CO_ID

    def test_sub_roles_solid_manager(self):
        from app.services.company_scope import sub_roles
        children = sub_roles('SOLID_LINE_MANAGER')
        assert 'DOTTED_LINE_MANAGER' in children
        assert 'EMPLOYEE' in children

    def test_sub_roles_employee_has_none(self):
        from app.services.company_scope import sub_roles
        assert sub_roles('EMPLOYEE') == []


class TestImportService:

    def test_parse_valid_csv(self):
        from app.services.import_service import parse_and_validate
        csv_bytes = b"first_name,last_name,email\nAnna,Smith,anna@test.com\n"
        with patch('app.services.import_service.query', return_value=None):
            rows, summary = parse_and_validate(csv_bytes, CO_ID)
        assert summary['row_count'] == 1
        assert summary['valid_count'] == 1
        assert summary['error_count'] == 0
        assert rows[0]['status'] == 'VALID'

    def test_parse_missing_required_column(self):
        from app.services.import_service import parse_and_validate
        csv_bytes = b"first_name,last_name\nAnna,Smith\n"
        rows, summary = parse_and_validate(csv_bytes, CO_ID)
        assert 'error' in summary
        assert rows == []

    def test_parse_invalid_email(self):
        from app.services.import_service import parse_and_validate
        csv_bytes = b"first_name,last_name,email\nAnna,Smith,not-an-email\n"
        with patch('app.services.import_service.query', return_value=None):
            rows, summary = parse_and_validate(csv_bytes, CO_ID)
        assert rows[0]['status'] == 'INVALID'
        assert summary['error_count'] == 1

    def test_parse_duplicate_email_in_file(self):
        from app.services.import_service import parse_and_validate
        csv_bytes = b"first_name,last_name,email\nAnna,Smith,dup@test.com\nBob,Jones,dup@test.com\n"
        with patch('app.services.import_service.query', return_value=None):
            rows, summary = parse_and_validate(csv_bytes, CO_ID)
        # Second row should be INVALID (duplicate)
        assert any(r['status'] == 'INVALID' for r in rows)

    def test_parse_invalid_employment_type(self):
        from app.services.import_service import parse_and_validate
        csv_bytes = b"first_name,last_name,email,employment_type\nAnna,Smith,a@b.com,ROBOT\n"
        with patch('app.services.import_service.query', return_value=None):
            rows, summary = parse_and_validate(csv_bytes, CO_ID)
        assert rows[0]['status'] == 'INVALID'


class TestSearchService:

    def test_search_org_reporting_to_me(self):
        from app.services.search_service import search_org
        result = search_org('show me people reporting to me', EMP_ID)
        assert result is not None
        assert result['action'] == 'focus_tree'
        assert result['root_id'] == EMP_ID

    def test_search_org_my_team(self):
        from app.services.search_service import search_org
        result = search_org('my team', EMP_ID)
        assert result is not None
        assert result['action'] == 'focus_tree'

    def test_search_org_no_match(self):
        from app.services.search_service import search_org
        result = search_org('hello world', EMP_ID)
        assert result is None

    def test_vacation_intent_upcoming(self):
        from app.services.search_service import _parse_vacation_intent
        assert _parse_vacation_intent('my upcoming vacation') == 'MY_UPCOMING'
        assert _parse_vacation_intent('team vacation')        == 'TEAM_UPCOMING'
        assert _parse_vacation_intent('all vacation')         == 'ALL_UPCOMING'
        assert _parse_vacation_intent('random query')         is None
