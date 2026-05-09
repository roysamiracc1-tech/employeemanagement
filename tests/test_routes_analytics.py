"""Unit tests for the analytics routes.

All service calls and DB interactions are mocked.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

# ── sample payloads the service would return ─────────────────────────────────

_OVERVIEW = {
    'totals': {'total_views': 420, 'unique_users': 35},
    'dau': [{'day': '2026-05-01', 'users': 12}],
    'top_pages': [{'page_label': 'My Vacation', 'route': '/vacation',
                   'views': 180, 'unique_users': 22}],
    'feature_adoption': [{'feature': 'Vacation Requests', 'users': 30,
                          'total_employees': 50, 'pct': 60.0}],
    'bulk_import': {'imports': 2, 'applied': 2, 'last_used': '2026-04-10'},
}

_VACATION = {
    'kpis': {'total': 45, 'approved': 35, 'rejected': 4, 'cancelled': 4,
             'pending': 2, 'approval_rate': 77.8, 'rejection_rate': 8.9,
             'cancellation_rate': 8.9, 'avg_decision_h': 3.5,
             'oldest_pending_days': 5},
    'over_time': [{'period': '2026-04', 'approved': 10, 'rejected': 1,
                   'cancelled': 1, 'pending': 0, 'total': 12}],
    'by_type': [{'type_name': 'Annual Leave', 'color': '#3b82f6',
                 'total': 40, 'approved': 32, 'pending': 2}],
    'utilisation': [{'group_name': 'Company Wide', 'employees': 50,
                     'used_days': 312}],
    'drilldown': [{'id': 'e-001', 'name': 'Sven Becker',
                   'job_title': 'Engineer', 'department': 'Engineering',
                   'location': 'Helsinki', 'manager_name': 'Liisa Virtanen',
                   'used_days': 3, 'period_requests': 1}],
    'group_by': 'company',
}

_SKILLS = {
    'kpis': {'total_employees': 50, 'with_skills': 38,
             'completeness_pct': 76.0, 'total_skill_entries': 200,
             'validated_entries': 120, 'validation_rate_pct': 60.0},
    'per_month': [{'period': '2026-04', 'added': 15}],
    'top_skills': [{'skill_name': 'Python', 'category': 'Engineering',
                    'employees': 25, 'validated': 18}],
    'by_dept': [],
    'emp_completeness': [{'id': 'e-001', 'name': 'Sven Becker',
                          'job_title': 'Engineer', 'department': 'Engineering',
                          'skill_count': 5, 'validated_count': 3}],
}

_ORG = {
    'kpis': {'total_employees': 50, 'active': 48, 'inactive': 2,
             'managers': 8, 'ics': 40, 'mgr_ratio': 16.7,
             'max_depth': 4, 'avg_span': 5.0},
    'by_dept': [{'department': 'Engineering', 'employees': 20}],
    'hc_over_time': [{'period': '2026-04', 'joined': 3, 'cumulative': 48}],
    'span_table': [{'manager_name': 'Liisa Virtanen',
                    'job_title': 'HR Manager', 'direct_reports': 6}],
    'org_views': [{'day': '2026-05-01', 'views': 10}],
    'org_view_total': {'total': 80, 'unique_users': 15},
}

_SEARCH = {
    'kpis': {'total_searches': 150, 'unique_searchers': 28,
             'zero_results': 12, 'avg_results': 4.2, 'zero_result_rate': 8.0},
    'volume': [{'day': '2026-05-01', 'searches': 10, 'zero_results': 1}],
    'top_terms': [{'query': 'python developer', 'searches': 15,
                   'avg_results': 3.0, 'zero_count': 0}],
    'zero_results': [{'query': 'parental leave', 'searches': 8}],
}


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_client(app):
    """Client logged in as SYSTEM_ADMIN with a company_id."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-admin-001'
            s['employee_id'] = 'emp-admin-001'
            s['company_id']  = 'co-001'
            s['roles']       = ['SYSTEM_ADMIN']
            s['user_name']   = 'Admin'
        yield c


@pytest.fixture
def portal_admin_client(app):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-portal-001'
            s['employee_id'] = 'emp-portal-001'
            s['company_id']  = 'co-001'
            s['roles']       = ['PORTAL_ADMIN']
            s['user_name']   = 'Portal Admin'
        yield c


@pytest.fixture
def hr_client(app):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-hr-001'
            s['employee_id'] = 'emp-hr-001'
            s['company_id']  = 'co-001'
            s['roles']       = ['HR_ADMIN']
            s['user_name']   = 'HR Admin'
        yield c


# ── page access tests ─────────────────────────────────────────────────────────

class TestAnalyticsPageAccess:
    def test_page_requires_login(self, client):
        r = client.get('/admin/analytics')
        assert r.status_code == 302

    def test_plain_employee_blocked(self, auth_client):
        r = auth_client.get('/admin/analytics')
        assert r.status_code == 302

    def test_system_admin_can_access(self, admin_client):
        with patch('app.routes.analytics.render_template', return_value='ok'), \
             patch('app.routes.analytics.query', return_value=[]):
            r = admin_client.get('/admin/analytics')
            assert r.status_code == 200

    def test_portal_admin_can_access(self, portal_admin_client):
        with patch('app.routes.analytics.render_template', return_value='ok'), \
             patch('app.routes.analytics.query', return_value=[]):
            r = portal_admin_client.get('/admin/analytics')
            assert r.status_code == 200

    def test_hr_admin_can_access(self, hr_client):
        with patch('app.routes.analytics.render_template', return_value='ok'), \
             patch('app.routes.analytics.query', return_value=[]):
            r = hr_client.get('/admin/analytics')
            assert r.status_code == 200


# ── overview API ─────────────────────────────────────────────────────────────

class TestAnalyticsOverview:
    def test_overview_requires_login(self, client):
        r = client.get('/api/analytics/overview')
        assert r.status_code == 302

    def test_overview_plain_employee_blocked(self, auth_client):
        r = auth_client.get('/api/analytics/overview')
        assert r.status_code == 302

    def test_overview_returns_data(self, admin_client):
        with patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW):
            r = admin_client.get('/api/analytics/overview?company_id=co-001&range=30d')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['totals']['total_views'] == 420
            assert len(d['feature_adoption']) == 1

    def test_overview_portal_admin_uses_own_company(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW) as mock_svc:
            r = portal_admin_client.get('/api/analytics/overview?range=30d')
            assert r.status_code == 200
            called_co = mock_svc.call_args[0][0]
            assert called_co == 'co-001'

    def test_overview_system_admin_no_company_returns_400(self, admin_client):
        with patch('app.routes.analytics.current_company_id', return_value=None):
            r = admin_client.get('/api/analytics/overview')
            assert r.status_code == 400


# ── vacation API ──────────────────────────────────────────────────────────────

class TestAnalyticsVacation:
    def test_vacation_returns_kpis(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_vacation_analytics',
                   return_value=_VACATION):
            r = portal_admin_client.get('/api/analytics/vacation?range=30d')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['kpis']['total'] == 45
            assert d['kpis']['approval_rate'] == 77.8

    def test_vacation_group_by_passed_to_service(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_vacation_analytics',
                   return_value=_VACATION) as mock_svc:
            portal_admin_client.get('/api/analytics/vacation?range=30d&group_by=department')
            assert mock_svc.call_args[0][3] == 'department'

    def test_vacation_hr_admin_allowed(self, hr_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_vacation_analytics',
                   return_value=_VACATION):
            r = hr_client.get('/api/analytics/vacation?range=30d')
            assert r.status_code == 200


# ── skills API ────────────────────────────────────────────────────────────────

class TestAnalyticsSkills:
    def test_skills_returns_completeness(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_skills_analytics',
                   return_value=_SKILLS):
            r = portal_admin_client.get('/api/analytics/skills?range=30d')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['kpis']['completeness_pct'] == 76.0
            assert d['kpis']['validation_rate_pct'] == 60.0

    def test_skills_drilldown_has_employee_names(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_skills_analytics',
                   return_value=_SKILLS):
            r = portal_admin_client.get('/api/analytics/skills?range=30d')
            d = json.loads(r.data)
            assert d['emp_completeness'][0]['name'] == 'Sven Becker'


# ── org API ───────────────────────────────────────────────────────────────────

class TestAnalyticsOrg:
    def test_org_returns_headcount_kpis(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_org_analytics',
                   return_value=_ORG):
            r = portal_admin_client.get('/api/analytics/org?range=30d')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['kpis']['active'] == 48
            assert d['kpis']['avg_span'] == 5.0
            assert d['kpis']['max_depth'] == 4

    def test_org_includes_page_view_stats(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_org_analytics',
                   return_value=_ORG):
            r = portal_admin_client.get('/api/analytics/org?range=30d')
            d = json.loads(r.data)
            assert d['org_view_total']['total'] == 80


# ── search API ────────────────────────────────────────────────────────────────

class TestAnalyticsSearch:
    def test_search_returns_zero_result_rate(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_search_analytics',
                   return_value=_SEARCH):
            r = portal_admin_client.get('/api/analytics/search?range=30d')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['kpis']['zero_result_rate'] == 8.0

    def test_search_zero_results_list(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_search_analytics',
                   return_value=_SEARCH):
            r = portal_admin_client.get('/api/analytics/search?range=30d')
            d = json.loads(r.data)
            assert d['zero_results'][0]['query'] == 'parental leave'


# ── CSV export ────────────────────────────────────────────────────────────────

class TestAnalyticsExport:
    def test_csv_export_vacation_returns_csv(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_vacation_analytics',
                   return_value=_VACATION):
            r = portal_admin_client.get(
                '/api/analytics/export/csv?section=vacation&range=30d')
            assert r.status_code == 200
            assert 'text/csv' in r.content_type
            assert b'Sven Becker' in r.data

    def test_csv_export_search_returns_csv(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_search_analytics',
                   return_value=_SEARCH):
            r = portal_admin_client.get(
                '/api/analytics/export/csv?section=search&range=30d')
            assert r.status_code == 200
            assert b'python developer' in r.data

    def test_csv_export_requires_login(self, client):
        r = client.get('/api/analytics/export/csv?section=vacation')
        assert r.status_code == 302


# ── date range parsing ────────────────────────────────────────────────────────

class TestAnalyticsDateParsing:
    def test_custom_date_range_accepted(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW) as mock_svc:
            portal_admin_client.get(
                '/api/analytics/overview?range=custom&start=2026-01-01&end=2026-03-31')
            import datetime
            call_start, call_end = mock_svc.call_args[0][1], mock_svc.call_args[0][2]
            assert call_start == datetime.date(2026, 1, 1)
            assert call_end   == datetime.date(2026, 3, 31)

    def test_invalid_custom_dates_fall_back_to_30d(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW) as mock_svc:
            import datetime
            portal_admin_client.get(
                '/api/analytics/overview?range=custom&start=bad&end=date')
            call_start = mock_svc.call_args[0][1]
            delta = (datetime.date.today() - call_start).days
            assert 28 <= delta <= 32


# ── feature gate ──────────────────────────────────────────────────────────────

class TestAnalyticsFeatureGate:
    """Verify that PORTAL_ADMIN / HR_ADMIN are blocked when feature is disabled,
    and SYSTEM_ADMIN always has access regardless."""

    def test_portal_admin_blocked_when_feature_disabled(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=False):
            r = portal_admin_client.get('/api/analytics/overview?range=30d')
            assert r.status_code == 403
            assert 'not enabled' in json.loads(r.data)['error'].lower()

    def test_hr_admin_blocked_when_feature_disabled(self, hr_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=False):
            r = hr_client.get('/api/analytics/vacation?range=30d')
            assert r.status_code == 403

    def test_portal_admin_allowed_when_feature_enabled(self, portal_admin_client):
        with patch('app.routes.analytics._analytics_enabled', return_value=True), \
             patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW):
            r = portal_admin_client.get('/api/analytics/overview?range=30d')
            assert r.status_code == 200

    def test_system_admin_always_allowed_even_when_feature_disabled(self, admin_client):
        """SYSTEM_ADMIN bypasses the gate — they manage the toggle."""
        with patch('app.routes.analytics._analytics_enabled', return_value=False), \
             patch('app.services.analytics_service.get_overview',
                   return_value=_OVERVIEW):
            r = admin_client.get('/api/analytics/overview?company_id=co-001&range=30d')
            assert r.status_code == 200

    def test_gate_applies_to_all_endpoints(self, portal_admin_client):
        endpoints = [
            '/api/analytics/overview?range=30d',
            '/api/analytics/vacation?range=30d',
            '/api/analytics/skills?range=30d',
            '/api/analytics/org?range=30d',
            '/api/analytics/search?range=30d',
            '/api/analytics/export/csv?section=vacation&range=30d',
        ]
        with patch('app.routes.analytics._analytics_enabled', return_value=False):
            for ep in endpoints:
                r = portal_admin_client.get(ep)
                assert r.status_code == 403, f'{ep} should return 403 when feature disabled'


class TestFeatureToggleAPI:
    """Tests for the SYSTEM_ADMIN feature toggle endpoints."""

    def test_toggle_requires_system_admin(self, portal_admin_client):
        r = portal_admin_client.post(
            '/api/admin/company-features/co-001/toggle',
            data=json.dumps({'feature_code': 'reports', 'enabled': True}),
            content_type='application/json',
        )
        assert r.status_code == 302   # redirected (role check fails)

    def test_toggle_unknown_feature_returns_400(self, admin_client):
        with patch('app.routes.analytics.query', return_value=None):
            r = admin_client.post(
                '/api/admin/company-features/co-001/toggle',
                data=json.dumps({'feature_code': 'nonexistent', 'enabled': True}),
                content_type='application/json',
            )
            assert r.status_code == 400

    def test_toggle_enable_returns_ok(self, admin_client):
        with patch('app.routes.analytics.query',
                   return_value={'id': 'feat-001'}), \
             patch('app.routes.analytics.execute'):
            r = admin_client.post(
                '/api/admin/company-features/co-001/toggle',
                data=json.dumps({'feature_code': 'reports', 'enabled': True}),
                content_type='application/json',
            )
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['ok'] is True
            assert d['enabled'] is True
            assert d['feature_code'] == 'reports'

    def test_toggle_disable_returns_ok(self, admin_client):
        with patch('app.routes.analytics.query',
                   return_value={'id': 'feat-001'}), \
             patch('app.routes.analytics.execute'):
            r = admin_client.post(
                '/api/admin/company-features/co-001/toggle',
                data=json.dumps({'feature_code': 'reports', 'enabled': False}),
                content_type='application/json',
            )
            assert r.status_code == 200
            assert json.loads(r.data)['enabled'] is False

    def test_get_company_features_requires_system_admin(self, portal_admin_client):
        r = portal_admin_client.get('/api/admin/company-features/co-001')
        assert r.status_code == 302

    def test_get_company_features_returns_list(self, admin_client):
        fake = [{'code': 'reports', 'label': 'Analytics',
                 'is_enabled': False, 'enabled_at': None,
                 'enabled_by_email': None}]
        with patch('app.routes.analytics.query', return_value=fake):
            r = admin_client.get('/api/admin/company-features/co-001')
            assert r.status_code == 200
            data = json.loads(r.data)
            assert isinstance(data, list)
